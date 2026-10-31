"""Run each version in its own interpreter to prevent module name collisions."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VERSIONS=[('v3_magnus_modular',20),('v4_abstract_opponents',15),('v5_four_player',21),
          ('v6_real_deck',21),('v7_rules',50),('v8_central',32),('v9_kernel',29),('v9b_live',34),('v9c_mana',49),('v10_priority',51),('v11_steps',50),('v12_combat',50),('v13_engines',69),('v14_lands',56),('v15_utility',38),('v16_channel',14),('v17_tutor',6),('v18_budget_deck',5),('v19_card_data',5),('v20_verified_types',4),('v21_early_mana',10),('v22_consider',8),('v23_medallion',13),('v24_reinforcements',9),('v25_personal_tutor',7),('v26_search',12),('v27_wizard_tutors',14),('v28_spellseeker',11),('v29_step_cycling',9),('v30_phyrexian_altar',10),('v31_premium_deck',15),('v32_cyclonic_rift',11),('v33_reiterate',12),('v34_mage_siege',14)]
for folder,expected in VERSIONS:
    path=ROOT/'simulator'/folder
    result=subprocess.run([sys.executable,'tests.py','-q'],cwd=path,text=True,capture_output=True)
    print(f'{folder}:',('PASS' if result.returncode==0 else 'FAIL'),f'(expected {expected} tests)')
    if result.returncode:
        print(result.stdout+result.stderr)
        raise SystemExit(result.returncode)
print('All thirty-four versioned suites completed successfully (774 tests expected).')

