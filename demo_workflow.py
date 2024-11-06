# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 17:22:41 2020

@author: Sylvain
"""

import stacktex.toolkit as st

#-----------------------------------------------------------------------------
# Main module material
TexFolder = 'raw_exe/main_module'
BankJSON = 'question_banks/question_bank_main.json'
buildFile_compendium = 'outputs_main_module/compendium.json'

buildFile_assessments = ['outputs_main_module/ict.json',
                            'outputs_main_module/exam.json',
                            'outputs_main_module/resit.json']

# buildFile_assessments = ['outputs_main_module/exam.json',
                          # 'outputs_main_module/resit.json']

# buildFile_assessments = ['outputs_main_module/exam.json']
# buildFile_assessments = ['outputs_main_module/resit.json']

workshopDir = 'outputs_main_module/workshop_material/'
buildFile_workshops = ['workshop_X/workshop_a.json',
                       'workshop_X/workshop_apps.json']

buildFile_revision = 'intensive/revision_quiz.json'

st.import_ex(TexFolder, BankJSON,'update')
# st.import_ex(TexFolder, BankJSON,'append')

st.build_tex(BankJSON, buildFile_compendium)

# for buildFile in buildFile_assessments:
#     st.build_tex(BankJSON, buildFile)
#     # st.build_xml(BankJSON, buildFile)

# for i in range(9):
#     for buildFileBase in buildFile_workshops:

#         buildFile = buildFileBase.replace('X',str(i+1))
#         st.build_tex(BankJSON, workshopDir + buildFile)
#         st.build_xml(BankJSON, workshopDir + buildFile)

# st.build_tex(BankJSON, workshopDir + buildFile_revision)
# st.build_xml(BankJSON, workshopDir + buildFile_revision)

buildFileBase = 'workshop_X/workshop_a.json'
buildFile = buildFileBase.replace('X',str(1))
st.build_tex(BankJSON, workshopDir + buildFile)
st.build_xml(BankJSON, workshopDir + buildFile)



# for buildFileBase in buildFile_workshops:

#     buildFile = buildFileBase.replace('X',str(1))
#     st.build_tex(BankJSON, workshopDir + buildFile)
#     # st.build_xml(BankJSON, workshopDir + buildFile)

#-----------------------------------------------------------------------------
# st.export_ex(BankJSON,'raw_exe')
# TexFolder = 'raw_exe/raw_exe/main_module'
# BankJSON2 = 'question_banks/question_bank_main_tol.json'
# buildFile_compendium = 'outputs_main_module/compendium_tol.json'

# st.import_ex(TexFolder, BankJSON2,'update')
# st.build_tex(BankJSON2, buildFile_compendium)
#-----------------------------------------------------------------------------
# # Value programme
# TexFolder = 'raw_exe/value'
# BankJSON = 'question_banks/question_bank_valuen'
# buildFile_compendium = 'outputs_value/compendium.json'

# workshopDir = 'outputs_value/'
# buildFileBase = 'workshop_X.json'

# st.import_ex(TexFolder, BankJSON,'update')
# st.build_tex(BankJSON, buildFile_compendium)

# for i in range(5):

#     buildFile = buildFileBase.replace('X',str(i+1))
#     st.build_tex(BankJSON, workshopDir + buildFile)
