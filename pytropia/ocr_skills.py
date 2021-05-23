import cv2
import numpy as np
import pytesseract
import imutils
import difflib
import sys
import sys
import os

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# pip install opencv-python

# TODO fix
# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

COLOR_RED = (0, 0, 255)

ALL_SKILLS = ["Agility","Health","Intelligence","Psyche","Stamina","Strength",
              "Beauty Sense","Body Sculpting","Face Sculpting","Hair Stylist",
              "Plastic Surgery","Quality Sense","Aim","Clubs","Combat Reflexes",
              "Combat Sense","Commando","Handgun","Heavy Melee Weapons",
              "Heavy Weapons","Inflict Melee Damage","Inflict Ranged Damage",
              "Kill Strike","Light Melee Weapons","Longblades","Marksmanship",
              "Martial Arts","Melee Combat","Melee Damage Assessment",
              "Power Fist","Ranged Damage Assessment","Rifle","Shortblades",
              "Support Weapon Systems","Weapons Handling","Whip","Wounding",
              "Armor Technology","Attachments Technology","BLP Weaponry Technology",
              "Blueprint Comprehension","Carpentry","Enhancer Technology",
              "Equipment Methodology","Explosive Projectile Weaponry Technology",
              "Gauss Weaponry Technology","Industrialist","Laser Weaponry Technology",
              "Machinery","Manufacture Armor","Manufacture Attachments",
              "Manufacture Electronic Equipment","Manufacture Enhancers",
              "Manufacture Mechanical Equipment","Manufacture Metal Equipment",
              "Manufacture Methodology","Manufacture Tools","Manufacture Vehicle",
              "Manufacture Weapons","Material Extraction Methodology",
              "Particle Beamer Technology","Plasma Weaponry Technology",
              "Spacecraft Engineering","Spacecraft Weaponry","Texture Engineering",
              "Tier Upgrading","Tools Technology","Vehicle Repairing","Vehicle Technology",
              "Weapon Technology","Wood Carving","Wood Processing","Avoidance","Dispense Decoy",
              "Dodge","Evade","Color Matching","Coloring","Coloring Methodology","Fashion Design",
              "Glamor","Make Textile","Material Comprehension","Surface Composition","Tailoring",
              "Texture Pattern Matching","Alertness","Athletics","Bravado","Coolness","Courage",
              "Dexterity","Intuition","Perception","Quickness","Serendipity","Butchering",
              "Mentor","Probing","Reaping","Reclaiming","Salvaging","Scan Animal","Scan Human",
              "Scan Mutant","Scan Robot","Scan Technology","Scavenging","Scourging","Skinning",
              "Anatomy","Diagnosis","Doctor","First Aid","Medical Therapy","Medicine","Treatment",
              "Bioregenesis","Concentration","Cryogenics","Electrokinesis","Ethereal Soul Language",
              "Force Merge","Jamming","Mindforce Harmony","Power Catalyst","Pyrokinesis","Sweat Gatherer",
              "Telepathy","Translocation","Archaeological Lore","Artefact Preservation","Drilling",
              "Drilling Expertise","Extraction","Geology","Ground Assessment","Metallurgy","Miner",
              "Mineral Sense","Mining","Precision Artefact Extraction","Prospecting","Resource Gathering",
              "Surveying","Treasure Sense","Analysis","Animal Lore","Animal Taming","Biology","Botany",
              "Computer","Deep Space Knowledge","Electronics","Engineering","Genetics","Mechanics",
              "Robotology","Scientist","Spacecraft Pilot","Spacecraft Systems","Xenobiology",
              "Zoology","Promoter Rating","Reputation"]

def add_points(a, b):
    return tuple(map(sum, zip(a, b)))

def scale_point(a, scale):
    return (round(a[0] * scale), round(a[1] * scale))

def crop(img, a, b):
    w = b[0] - a[0]
    h = b[1] - a[1]
    x = a[0]
    y = a[1]
    return img[y:y+h, x:x+w]

# Remove 'margin' pixels
def margin(img, margin_x, margin_y):
    h, w, _ = img.shape
    return crop(img, (margin_x, margin_y), (w - margin_x, h - margin_y))

def ocr_page_number(img):
    # psm 7 = "Treat the image as a single text line."
    chars = '0123456789/'
    result = pytesseract.image_to_string(img, lang='eng', config=f'-c tessedit_char_whitelist="{chars}" --psm 7')
    return result.partition('\n')[0].split('/')

def ocr_total_skills(img):
    # psm 8 = Treat the image as a single word.
    chars = '0123456789'
    result = pytesseract.image_to_string(img, lang='eng', config=f'-c tessedit_char_whitelist="{chars}" --psm 8')
    return result.partition('\n')[0]

def ocr_skill_name(img):
    # Might be better to match the icon instead... Will wait for "now UI" though.
    # Currently the detection doesn't work if the skills window isn't focused

    # Convert to gray scale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold
    _, img = cv2.threshold(img, 130, 255, cv2.THRESH_BINARY)

    #cv2.imshow('Matched Template', img)
    #cv2.waitKey(0)

    # psm 7 = "Treat the image as a single text line."
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '
    result = pytesseract.image_to_string(img, lang='eng', config=f'-c tessedit_char_whitelist="{chars}" --psm 7')
    result = result.partition('\n')[0]
    #eprint(result)
    result = difflib.get_close_matches(result, ALL_SKILLS)

    if len(result) < 1:
        return ""

    return result[0]

# Was not able to get reliable OCR with Tesseract because of the chaning background.
# This code instead matches number
def ocr_skill_points(img, i, numbers, scale):
    # Where are the digits
    digit_positions = [437, 465, 493, 521, 550]
    digit_positions = [i * scale for i in digit_positions]
    digit_best_match = [0, 0, 0, 0, 0]

    num_digits = len(digit_positions)
    digit_margin = 5 # +/-
    digits = [0, 0, 0, 0, 0]

    # Parameters for image pre-processing
    scale_percent = 400
    threshold = 170

    # Upscale
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    img_pre = cv2.resize(img, dim, interpolation = cv2.INTER_CUBIC)
    # Convert to gray scale
    img_pre = cv2.cvtColor(img_pre, cv2.COLOR_BGR2GRAY)

    # Threshold
    # Currently the detection doesn't work if the skills window isn't focused
    _, img_pre = cv2.threshold(img_pre, threshold, 255, cv2.THRESH_BINARY)

    #cv2.imshow('Matched Template', img_pre)    
    #cv2.waitKey(0)

    # Loop over each digit template
    for i in range(10):
        # Match digit
        res = cv2.matchTemplate(img_pre, numbers[i], cv2.TM_CCOEFF_NORMED)
        __name__, w = numbers[i].shape

        # Loop over different detection thresholds to find the best one
        # for each digit position.
        for thres in np.arange(0.5, 0.9, 0.1):
            loc = np.where(res >= thres) # Detection threshold
            for pt in zip(*loc[::-1]):
                # For each match check where the digit is positioned
                xpos = round(pt[0] + w / 2)
                #eprint(xpos)
                for d in range(num_digits):
                    # If the digit matches a position, update digits
                    if xpos > digit_positions[d] - digit_margin and \
                       xpos < digit_positions[d] + digit_margin and \
                       digit_best_match[d] < thres:
                        digits[d] = i
                        digit_best_match[d] = thres
                        break
                    # Debug code
                    #eprint(f"{i} found at {xpos}")
                    #eprint(f"{digits}")
                    #cv2.rectangle(
                    #    img, (xpos, pt[1]), (xpos + 1, pt[1] + 1), (127, 127, 127), 2)

    #print(digit_best_match)
    # Convert digit positions to a number
    retval = 0
    for d in range(num_digits):
        retval += digits[d] * 10 ** (num_digits - d - 1)

    #if retval == 0:
    #    raise Exception("Failed to parse digits!")

    # Parse fractional part
    # Start search at start point pixel
    # Find pixel where value first exceeds pixel_threshold,
    # then look for pixel where it's under pixel_threshold again
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    progression_per_pixel = 0.00775 / scale # approximated based on real data, assumes linear progress.
    pixel_threshold = 80
    start_x = round(5 * scale)
    y = round(10 * scale)
    start=0
    stop=0
    for i in range(start_x, img.shape[1] - 1, 1):
        pixel_value = img[y, i]
        if start == 0 and pixel_value > pixel_threshold:
            start = i
        elif start != 0 and stop == 0 and pixel_value < pixel_threshold:
            stop = i
            break

    progression = (stop - start - 1) * progression_per_pixel
    retval = retval + progression
    #eprint(f"stop {stop} start {start} progression {progression} foo {progression_per_pixel}")

    #debug code
    #cv2.imshow('Matched Template', img)
    #cv2.imwrite("foo.png", img)
    #cv2.waitKey(0)

    return retval


# TODO: argument parsing
def from_image(image):
    data = {}
    data['skills'] = {}
    debug = False

    skill_page = cv2.imread(image)
    #skill_page = cv2.imread('test.png')

    template_skills = cv2.imread(os.path.join(os.path.dirname(__file__), 'marks/skill-mark-1.png'))

    # TODO: Do we need to match with scaling to handle DPI differences?
    # Test scale 100%, 125%, 150% and 200%, find best match
    for scale in range(100, 200, 25):
        resized = imutils.resize(template_skills, width = int(template_skills.shape[1] * (scale/100)))
        res = cv2.matchTemplate(skill_page, resized,cv2.TM_CCOEFF_NORMED)

        loc = np.where( res >= 0.8)
        if len(list(zip(*loc[::-1]))) > 0:
            #eprint(f"found with scale: {scale} %")
            break

    scale = scale / 100
    if debug:
        eprint(f"Scale: {scale}")
    data['scale'] = scale

    skills_per_page = 7
    skill_height = 31.5 * scale
    name_width = round(220 * scale)
    point_width = round(154 * scale)
    first_name_offset = scale_point((-69, 25), scale)
    first_point_offset =  scale_point((309, 25), scale)

    total_skills_offset =  scale_point((82, -28), scale)
    total_skills_height = round(15 * scale)
    total_skills_width = round(60 * scale)

    page_number_offset =  scale_point((127, 252), scale)
    page_number_height = round(16 * scale)
    page_number_width = round(55 * scale)

    # Buttons to enable "auto mode"
    forward_button_offset =  scale_point((100, 264), scale)
    back_button_offset = scale_point((210, 264), scale)

    numbers  = []
    for i in range(10):
        filename = os.path.join(os.path.dirname(__file__), f'numbers/{i}.png')
        numbers.append(cv2.cvtColor(cv2.imread(filename), cv2.COLOR_BGR2GRAY))

    if scale > 1:
        template_skills = imutils.resize(template_skills, width = int(template_skills.shape[1] * scale))

        for i in range(10):
            numbers[i] = imutils.resize(numbers[i], width = int(numbers[i].shape[1] * scale))

    h, w, _ = template_skills.shape

    res = cv2.matchTemplate(skill_page, template_skills, cv2.TM_CCOEFF_NORMED)

    _, max_val, _, origin_top_left = cv2.minMaxLoc(res)

    if max_val < 0.8:
        raise Exception("Unable to find skill window")

    skill_page_annotate = np.copy(skill_page)
    cv2.rectangle(skill_page_annotate, origin_top_left, add_points(origin_top_left, (w, h)), color=COLOR_RED, thickness=1)

    for i in range(0, skills_per_page, 1):
        # Skill names
        top_left = add_points(origin_top_left, first_name_offset)
        top_left = add_points(top_left, (0, round(skill_height * i)))
        bottom_right =  add_points(top_left, (name_width, round(skill_height-0.5)))
        cv2.rectangle(skill_page_annotate, top_left, bottom_right, color=COLOR_RED, thickness=1)
        crop_img = margin(crop(skill_page, top_left, bottom_right), 2, 8)

        skill_name = ocr_skill_name(crop_img)

        if len(skill_name) == 0:
            continue

        # Skill points
        top_left = add_points(origin_top_left, first_point_offset)
        top_left = add_points(top_left, (0, round(skill_height * i)))
        bottom_right =  add_points(top_left, (point_width, round(skill_height-0.5)))
        cv2.rectangle(skill_page_annotate, top_left, bottom_right, color=COLOR_RED, thickness=1)
        crop_img = crop(skill_page, top_left, bottom_right)

        skill_points = ocr_skill_points(crop_img, i, numbers, scale)

        data['skills'][skill_name] = skill_points
        if debug:
            eprint(f"{skill_name}: {skill_points}")

    # Total skills
    top_left = add_points(origin_top_left, total_skills_offset)
    bottom_right =  add_points(top_left, (total_skills_width, total_skills_height))
    cv2.rectangle(skill_page_annotate, top_left, bottom_right, color=COLOR_RED, thickness=1)
    crop_img = crop(skill_page, top_left, bottom_right)
    total_skills = ocr_total_skills(crop_img)
    data['total-skills'] = total_skills

    # Page number
    top_left = add_points(origin_top_left, page_number_offset)
    bottom_right =  add_points(top_left, (page_number_width, page_number_height))
    cv2.rectangle(skill_page_annotate, top_left, bottom_right, color=COLOR_RED, thickness=1)
    crop_img = crop(skill_page, top_left, bottom_right)
    page_info = ocr_page_number(crop_img)
    data['page'] = page_info[0]
    data['num-pages'] = page_info[1]

    if debug:
        eprint(f"Total skills: {total_skills}")
        eprint(f"Page number: {page_info}")
        cv2.imwrite("match.png", skill_page_annotate)
        cv2.imshow('Matched Template', skill_page_annotate)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return data
