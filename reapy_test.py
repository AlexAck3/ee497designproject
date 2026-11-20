import reapy
from reapy import reascript_api as RPR

project = reapy.Project()
track = project.tracks[0]

gain = 3  # dB
result = RPR.TrackFX_SetEQParam(track.id, 0, 2, 0, 1, gain, False)
print(f"EQ Output: {result}")