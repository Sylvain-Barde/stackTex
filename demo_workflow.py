# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 17:22:41 2020

@author: Sylvain

Contests of the ./demo/ folder:

demo/
├── __init__.py
├── LICENSE
├── requirements.txt
├── demo_workflow.py
├── toolkit.py
├── dependencies.py
├── snippets.json
├── README.md
├── demo/
│   └── buildFiles/
│       ├── compendium.json
│       └── maths_seminar.json
├── latex_exercise_template/
│   ├── tex_template.pdf
│   └── tex_template.pdf
└── templates/
    ├── compendium.tex
    ├── seminar.tex
    ├── stack.xml
    └── test.tex

"""

import stacktex.toolkit as st

#-----------------------------------------------------------------------------
# Path to raw exercises
TexFolder = 'demo/raw_latex_exercises'

# Path to save question bank as a JSON
BankJSON = 'demo/question_bank.json'

# path to buildfiles
buildFile_compendium = 'demo/buildFiles/compendium.json'
buildFile_examples = ['outputs_main_module/ict.json',
                            'outputs_main_module/exam.json',
                            'outputs_main_module/resit.json']

#-----------------------------------------------------------------------------
# Import raw exercises into the question bank
st.import_ex(TexFolder, BankJSON,'update')

# Build compendium of all exercises in the question bank
st.build_tex(BankJSON, buildFile_compendium)

# Build examples as PDF and XML outputs
for buildFile in buildFile_examples:
    st.build_tex(BankJSON, buildFile)
    st.build_xml(BankJSON, buildFile)
#-----------------------------------------------------------------------------
