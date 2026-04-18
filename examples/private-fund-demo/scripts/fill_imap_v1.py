import os, sys
_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_DIR, '../../..')
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
from fill_utils import run_fill

from scenes_part0a import fill_a1, fill_a2
from scenes_part0b import fill_b1, fill_b2
from scenes_part1 import fill_c1

TARGET = os.path.join(_DIR, '../deliverables/imap-private-fund-v1.html')

run_fill(TARGET, [
    ('scene-a-1', fill_a1),
    ('scene-a-2', fill_a2),
    ('scene-b-1', fill_b1),
    ('scene-b-2', fill_b2),
    ('scene-c-1', fill_c1),
])
