from MeetnetVlaamseBankenLib import *
from cmath import rect, phase
from math import radians, degrees
import os

# Meetnet Vlaamse Banken login:
username = os.environ.get("GMAIL")
password = os.environ.get('MEETBANK_PASS')

# IFTTT key
webhookskey = os.environ.get("IFTTT_KEY")

# Calibrations
Coast_SW_limit = 230
Coast_NE_limit = 50
WindSpeedKnotsMin = 7
WindSpeedKnotsMax = 28

# Conversions
mps_knots = 1.943844

# -- Functions --

# Processing of the wind direction
# Input: list of wind directions
# Output:
# - WindDirectionOk for kitesurfing?
# - Mean angle wind direction
# - Minimum angle wind direction
# - Maximum angle wind direction
# - Delta minimum and maximum angle wind direction
def ProcessWindDirection(WindDirectionTab):
    # Calculate average wind direction
    Mean_angle = mean_angle(WindDirectionTab)
    # Calculate min/max wind direction and delta angle
    min_average = [0, 0]
    plus_average = [0, 0]
    for entry in WindDirectionTab:
        delta = ((entry%360 - Mean_angle%360) + 180) % 360 - 180
        if delta < min_average[0]:
            min_average[0] = delta
            min_average[1] = entry
        if delta > plus_average[0]:
            plus_average[0] = delta
            plus_average[1] = entry
    # Set to false when the wind is off shore
    WindDirectionConditionOK_b = True
    for entry in WindDirectionTab:
        if entry >= Coast_NE_limit and entry <= Coast_SW_limit:
            WindDirectionConditionOK_b = False
    return WindDirectionConditionOK_b, Mean_angle, min_average[1], plus_average[1], plus_average[0]-min_average[0]

# Processing of the wind speed
# Input:
# - Wind speed table (m/s)
# - Metric for output: 0 = m/s, 1 = knots
# Output:
# - Average wind speed
# - Max wind speed
# - Min wind speed
# - Delta
def ProcessWindSpeed(WindSpeedTab, metric):
    AverageWindSpeed = sum(WindSpeedTab)/len(WindSpeedTab)
    MaxWindSpeed = max(WindSpeedTab)
    MinWindSpeed = min(WindSpeedTab)
    DeltaWindSpeed = MaxWindSpeed - MinWindSpeed
    WindSpeedConditionOk_b = True
    if (AverageWindSpeed*mps_knots < WindSpeedKnotsMin or AverageWindSpeed*mps_knots > WindSpeedKnotsMax):
        WindSpeedConditionOk_b = False
    if metric == 1:
        return WindSpeedConditionOk_b, AverageWindSpeed*mps_knots, MaxWindSpeed*mps_knots, MinWindSpeed*mps_knots, DeltaWindSpeed*mps_knots
    else:
        return WindSpeedConditionOk_b, AverageWindSpeed, MaxWindSpeed, MinWindSpeed, DeltaWindSpeed

# Determine mean angle
def mean_angle(deg):
    angle = degrees(phase(sum(rect(1, radians(d)) for d in deg)/len(deg)))
    if angle < 0:
        return 360 + angle
    else:
        return angle

# Convert wind angle to wind direction
def convert_to_winddirection(angle):
    windsectors = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW","N"]
    index = int(round(angle/22.5, 0))
    return windsectors[index]

# IFTTT
def IFTTT(value1, value2):
    report = {}
    report['value1'] = f"Let's go kitesurfing!! \nWind direction: {str(value1)} \nWind speed: {str(value2)} knots"
    IFTTT_url = f'https://maker.ifttt.com/trigger/KiteSurfCheck/with/key/{webhookskey}'
    r = requests.post(IFTTT_url, data = report)
    return r.status_code

# -- Main --
if __name__ == "__main__":
    VlaamseMeetbank = VlaamseMeetbank(username, password)
    Data = VlaamseMeetbank.getDataLastXhours(2,["NP7WRS", "NP7WVC"])
    WindDirectionTab = []
    WindSpeedTab = []
    for Entry in Data['Values']:
        if Entry['ID'] == "NP7WRS":
            for sample in Entry['Values']:
                WindDirectionTab.append(sample['Value'])
        if Entry['ID'] == "NP7WVC":
            for sample in Entry['Values']:
                WindSpeedTab.append(sample['Value'])

    # Wind direction processing
    a1, a2, a3, a4, a5 = ProcessWindDirection(WindDirectionTab)
    # Wind speed processing
    b1, b2, b3, b4, b5 = ProcessWindSpeed(WindSpeedTab, 1)

    # Only send message when the conditions are OK to kitesurf!
    if(a1 and b1):
        print("Conditions are OK for kitesurfing!!!")
        r = IFTTT(convert_to_winddirection(a2), round(b2,0))
    else:
        print("Conditions are NOK for kitesurfing!!!")