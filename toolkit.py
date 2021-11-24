# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 15:45:56 2020

@author: Sylvain
"""

import json
import re
import os
import subprocess
import inspect
import random

from .dependencies import decimalCheck, genParams, get_fieldName, logCheck
from .dependencies import parseTex, parseTexEnv, processParamFuncs, paramSub
from .dependencies import safesub, sorted_nicely, symbParse, pad
from .dependencies import trim, xmlParse

#------------------------------------------------------------------------------
def import_ex(TexFolder,BankJSON,mode = 'append'):

    print('\nImporting Latex exercises to JSON question bank\n')

    # Check if there is a pre-existing question bank to append work
    source_dict = {}
    if os.path.isfile(BankJSON):

        # Mode check
        if mode not in ['update','append']:
            print("Incorrect mode selection '{:s}'".format(mode))
            print("Defaulting to 'append' mode\n")
            mode = 'append'

        # Load question bank, list sources and find next tag
        with open(BankJSON) as f:
            json_str = f.read()
            exBank = json.loads(json_str)
        f.close
        ex_list = [*exBank.keys()]

        currTag = 0
        for ex in ex_list:
            ex_tag = exBank[ex]['tag']
            source_dict[exBank[ex]['source']] = ex_tag
            currTag = max(currTag,ex_tag)

        print('  Using existing question bank: ' + BankJSON)
        if mode == 'update':
            print('  Update mode, all exercises in bank can be owerwritten\n')
        elif mode == 'append':
            print('  Append mode, only new exercises will be added to bank\n')

    else:

        # Generate empty Dict structure for question bank
        exBank = {}
        currTag = 0

        mode = 'update'
        print('  No existing question bank in location: ' + BankJSON)
        print('  Creating new question bank\n')

    # -------------------------------------------------------------------------
    keyMap = {"category":"category",
              "subCategory":"subCategory",
              "exerciseParameters":"params",
              "decimalPlaces":"decimalPlaces",
              "questionFormat":["questions","format"],
              "feedbackFormat":["solutions","format"],
              "questionBlurb":["questions","blurb"],
              "feedbackBlurb":["solutions","blurb"],
              "questionType":["questions","types",[]],
              "questionText":["questions","items",[]],
              "feedbackText":["solutions","feedback",[]],
              "prompt":["questions","prompts",[]],
              "tolerance":["solutions","tolerance",[]],
              "solution":["solutions","items",[]],
              "mark":["questions","marks",[]]}
    # -------------------------------------------------------------------------

    # Explore tex exercises folder to extract filenames
    # Will ignore any non-Tex file
    files = []
    for r, d, f in os.walk(TexFolder):      # r=root, d=directories, f=files

        for file in sorted_nicely(f):
            if '.tex' in file:
                files.append(os.path.join(r, file))

    if not os.path.exists(TexFolder):
        print("  Folder '" + TexFolder + "' does not exist")
    elif files == []:
        print("  Folder '" + TexFolder + "' contains no .tex files")

    # Process all exercises in the list
    usedFiles = []
    unusedFiles = []
    for file in files:

        # Load Latex exercise format
        with open(file) as f:
            ExStr = f.read()
        f.close

        # Check if exercise is already in the bank, if so re-use tag
        cleanFile = re.sub('\\\\','/',file)
        if cleanFile in source_dict.keys():
            WrkDict = {'tag' : source_dict[cleanFile]}
        else:
            currTag+=1
            WrkDict = {'tag' : currTag}
        WrkDict['source'] = cleanFile

        # Break Latex exercise into lines and process
        ExLines = ExStr.splitlines()
        WrkStr = ""
        isActive = False                # Parsing initially inactive
        keys = ''                       # Initialise empty dict key

        for line in ExLines:

            if not line[0:1] == "%":    # Parse non-commented lines only

                if r'\fieldname{' in line or r'\end{document}' in line:

                    if isActive:        # If active, append strings to dict

                        if type(keys) is str:

                            WrkDict[keys] = trim(WrkStr)

                        elif type(keys) is list:

                            if keys[0] not in WrkDict:
                                WrkDict[keys[0]] = {}

                            if len(keys) == 3 and \
                                    keys[1] not in WrkDict[keys[0]]:
                                WrkDict[keys[0]][keys[1]] = []

                            if len(keys) == 2:
                                WrkDict[keys[0]][keys[1]] = trim(WrkStr)

                            elif len(keys) == 3:
                                WrkDict[keys[0]][keys[1]].append(trim(WrkStr))

                        WrkStr = ""     # Reset working line

                    else:               # Activate parsing on 1st encounter

                        isActive = True

                    if r'\fieldname{' in line:
                        fieldName = get_fieldName(line)
                        keys = keyMap[fieldName]

                # Only append lines to working line if parsing is active
                elif isActive:

                    WrkStr = WrkStr + '\n' + line

        # Save question to bank, depending on mode
        if mode == 'update' or (
                mode == 'append' and cleanFile not in source_dict.keys()):
            bankKey = "Ex_" + str(WrkDict["tag"])
            exBank[bankKey] = WrkDict  # Append dict to stored dict
            usedFiles.append(file)
            print('  Importing: ' + file)
        else:
            unusedFiles.append(file)
            print('  Already in bank: ' + file)


    with open(BankJSON, 'w') as f_out:
        json_outstr = json.dumps(exBank,indent=4)
        f_out.write(json_outstr)
    f_out.close

    print('\n  Done, {:d} files processed'.format(len(files)))
    print('    Unchanged: {:d} '.format(len(unusedFiles)))
    print('    Imported:  {:d} '.format(len(usedFiles)))

    return None

#------------------------------------------------------------------------------
def export_ex(BankJSON,outFolder):

    with open(BankJSON) as f:                       # Load question bank
        json_str = f.read()
        exBank = json.loads(json_str)
    f.close

    if not os.path.exists(outFolder):
        print('  Creating export folder ' + outFolder)
        os.makedirs(outFolder,mode=0o777)
    else:
        print('  Using export folder ' + outFolder)

    head, tail = os.path.split(inspect.getsourcefile(import_ex))
    with open(os.path.join(head,'snippets.json')) as f:          # Load formats
        json_str = f.read()
        snippets_all = json.loads(json_str)
        snippets = snippets_all['tex']
    f.close

    exLabels = list(exBank.keys())
    for exLabel in exLabels:

        ex = exBank[exLabel]
        templateStr = snippets['Template']['header']
        outName = outFolder + '/' + ex['source']

        print('  Exporting ' + outName)

        # Required components
        texItem = trim(parseTex(ex['category']))
        templateStr = re.sub('CatStr',texItem,templateStr)
        texItem = trim(parseTex(ex['subCategory']))
        templateStr = re.sub('SubCtStr',texItem,templateStr)
        texItem = trim(parseTex(ex['questions']['format']))
        templateStr = re.sub('QuFrmtStr',texItem,templateStr)
        texItem = trim(parseTex(ex['solutions']['format']))
        templateStr = re.sub('SolFrmtStr',texItem,templateStr)
        texItem = trim(parseTex(ex['questions']['blurb']))
        templateStr = re.sub('QuBlrb',texItem,templateStr)
        texItem = trim(parseTex(ex['solutions']['blurb']))
        templateStr = re.sub('SolBlrb',texItem,templateStr)

        QuTypeList = list(ex['questions']['types'])
        QuTxtList = list(ex['questions']['items'])
        PrmptStrList = list(ex['questions']['prompts'])
        SolStrList = list(ex['solutions']['items'])
        TolStrList = list(ex['solutions']['tolerance'])
        MarkStrList = list(ex['questions']['marks'])

        # Optional components
        if 'params' in ex.keys():
            texItem = trim(parseTex(ex['params']))
            templateStr = re.sub('ParamStr',texItem,templateStr)
        else:
            templateStr = re.sub(r'\\fieldname\{exerciseParameters\}\n',
                                 '',templateStr)
            templateStr = re.sub('ParamStr\n\n','',templateStr)

        if 'decimalPlaces' in ex.keys():
            texItem = trim(parseTex(ex['decimalPlaces']))
            templateStr = re.sub('DecPlaces',texItem,templateStr)
        else:
            templateStr = re.sub(r'\\fieldname\{decimalPlaces\}\n',
                                 '',templateStr)
            templateStr = re.sub('DecPlaces\n\n','',templateStr)

        if 'feedback' in ex['solutions'].keys():
            SolTxtList = list(ex['solutions']['feedback'])

        # if 'tolerance' in ex['solutions'].keys():
        #     TolStrList = list(ex['solutions']['tolerance'])
        # else:
            # TolStrList = ['']*len(QuTxtList)

        ItemStr = ''
        for QuTypeItem in QuTypeList:

            ItemStrBase = parseTex(snippets['Template']['item'])

            texItem = trim(parseTex(QuTypeItem))
            ItemStrBase = re.sub('QuType',texItem,ItemStrBase)
            texItem = trim(parseTex(QuTxtList.pop(0)))
            ItemStrBase = re.sub('QuTxt',texItem,ItemStrBase)
            texItem = trim(parseTex(PrmptStrList.pop(0)))
            ItemStrBase = re.sub('PrmptStr',texItem,ItemStrBase)
            texItem = trim(parseTex(SolStrList.pop(0)))
            ItemStrBase = re.sub('SolStr',texItem,ItemStrBase)
            # texItem = trim(parseTex(TolStrList.pop(0)))
            # ItemStrBase = re.sub('TolStr',texItem,ItemStrBase)
            texItem = trim(parseTex(MarkStrList.pop(0)))
            ItemStrBase = re.sub('MarkStr',texItem,ItemStrBase)

            if 'feedback' in ex['solutions'].keys():
                texItem = trim(parseTex(SolTxtList.pop(0)))
                ItemStrBase = re.sub('SolTxt',texItem,ItemStrBase)
            else:
                ItemStrBase = re.sub('SolTxt','',ItemStrBase)
                ItemStrBase = re.sub(r'\fieldname{feedbackText}',
                                 '',ItemStrBase)
                # ItemStrBase = re.sub('DecPlaces\n\n','',ItemStrBase)
            if 'tolerance' in ex['solutions'].keys():
                texItem = trim(parseTex(TolStrList.pop(0)))
                ItemStrBase = re.sub('TolStr',texItem,ItemStrBase)
            else:
                ItemStrBase = re.sub('TolStr','',ItemStrBase)

            ItemStr += ItemStrBase

        templateStr = re.sub('ItemStr',ItemStr,templateStr)

        # Reverse safe substition of backslash
        templateStr = re.sub('¬','\\\\',templateStr)

        # Write exercises to file
        save_path = outName.split("/")
        save_path = os.path.join(*save_path[0:-1])
        if not os.path.exists(save_path):
            os.makedirs(save_path,mode=0o777)

        with open(outName, 'w') as f_out:
            f_out.write(templateStr)
        f_out.close

    return None

#------------------------------------------------------------------------------
def build_tex(BankJSON,build_file):

    print('\nBuilding Latex and PDF from build file\n')

    # Load assets
    with open(build_file) as f:        # Load build instructions
        json_str = f.read()
        setup = json.loads(json_str)
    f.close

    with open(BankJSON) as f:          # Load question bank
        json_str = f.read()
        exBank = json.loads(json_str)
    f.close

    head, tail = os.path.split(inspect.getsourcefile(import_ex))
    with open(os.path.join(head,'snippets.json')) as f:          # Load formats
        json_str = f.read()
        snippets_all = json.loads(json_str)
        snippets = snippets_all['tex']
    f.close

    #--------------------------------------------------------------------------
    # Pop the meta-data out of the dictionary, configure runs.
    # Depends on whether or not an exercise list is provided

    filename = setup.pop('filename')            # Chosen file name
    if 'exList' in setup:
        template = setup.pop('template')        # Choice of template
        exListBase = setup.pop('exList')        # List of exercises from bank

        if 'seed' in setup:                     # Extract random seed if there
            seed = setup.pop('seed')
        else:
            seed = 0

        if 'marks' in setup:                    # Include Marks flag
            markFlag = setup.pop('marks')
            if not isinstance(markFlag,bool):   # Must be boolean
                markFlag = False
        else:
            markFlag = False

        if 'verbose' in setup:                  # Verbose feedback flag
            verbose = setup.pop('verbose')
            if not isinstance(verbose,bool):    # Must be boolean
                verbose = True
        else:
            verbose = True

        if 'newPage' in setup:                  # New page per question flag
            newPageFlag = setup.pop('newPage')
            if not isinstance(newPageFlag,bool): # Must be boolean
                newPageFlag = False
        else:
            newPageFlag = False

        outNames = [filename + '.tex',filename + '_solutions.tex']
        solFlagRuns = [[False],[False,True]]
        compendFlag = False


    else:
        template = 'compendium.tex'             # Choose report template
        compendFlag = True
        outNames = [filename + '.tex']
        solFlagRuns = [[False,True]]            # Only a single run, with Q&A

        if 'seed' in setup:                     # Extract random seed if there
            seed = setup.pop('seed')
        else:
            seed = 0
        markFlag = True                         # Mark flag set to true
        verbose = True                          # Verbose flag set to true
        newPageFlag = False                     # New page set to false

        exData = []
        for ex_label in exBank.keys():

            ex = exBank[ex_label]
            exData.append((ex['category'],ex['subCategory'],ex_label))

        # Sort exercises by category and subcategory (labels already sorted)
        sortedEx = sorted(exData,key=lambda item: item[1])
        sortedEx = sorted(sortedEx,key=lambda item: item[0])

        exList = []
        for ex in sortedEx:
            exList.append(ex[2])

        exListBase = []
        exListBase.append(exList)
        laggedCat = ''
        laggedSubCat =''

    #--------------------------------------------------------------------------
    # Perform compilation runs
    for outName in outNames:

        solFlag = solFlagRuns.pop(0)

        print('  Build file: ' + outName)
        random.seed(seed)

        # Load corresponding template
        with open(os.path.join(head,'templates',template)) as f:
            templateStr = f.read()
        f.close

        # Replace fields in template by data remaining in the instruction json
        for key in setup.keys():
            templateStr = safesub(key,setup[key],templateStr)

        # Add exercises from list to the exercise string array
        sectionCount = 1
        for exList in exListBase:

            ExStr = []
            for exLabel in exList:

                print('  Processing {:s}'.format(exLabel))

                ex = exBank[exLabel]

                if compendFlag:         # If full compendium, append category
                    metadata = sortedEx.pop(0)
                    Cat = metadata[0]
                    SubCat = metadata[1]
                    if not Cat == laggedCat:
                        ExStr.append('\\chapter{'+ Cat +'}\n')    # New chapter
                        laggedCat = Cat
                    if not SubCat == laggedSubCat:
                        ExStr.append('\\section{'+ SubCat +'}\n') # New section
                        laggedSubCat = SubCat

                    cleanLbl = re.sub('_','\\_',exLabel)
                    ExStr.append(
                            '\\subsection{Exercise \\texttt{'+cleanLbl+'}}\n')
                    cleanSource = re.sub('\\\\','¬',ex['source'])
                    cleanSource = re.sub('_','\\_',cleanSource)
                    ExStr.append('source: \\texttt{' + cleanSource +'}\n\n')
                    if 'params' in ex.keys():
                        ExStr.append(
                            'Randomised parameters in \\textbf{bold}. \n\n')
                    else:
                        ExStr.append(
                            'No randomised parameters in exercise. \n\n')

                    # Append link back to table of contents
                    ExStr.append('\\hyperlink{contents}{Back to Table of Contents}\n')

                    # Start enumerating question components
                    ExStr.append('\\begin{top_enumerate}\n')

                for SolutionFlag in solFlag:

                    if SolutionFlag:                                # Add items

                        ExStr.append('\\addtocounter{enumi}{-1}\n')
                        content = ex['solutions']

                        # if 'feedback' in content:
                        if 'feedback' in content and verbose == True:
                            items = content['feedback']
                        else:
                            prompts = ex['questions']['prompts']
                            sols = list(content['items'])
                            items = []
                            for prompt in prompts:

                                if prompt == '':
                                    eqsign = ''
                                else:
                                    eqsign = '='

                                solStr = '$' + re.sub('\$','',prompt) + \
                                    eqsign + '{' + re.sub(
                                        '\$','', sols.pop(0)) +'}' + '$'
                                items.append(solStr)

                    else:
                        content = ex['questions']
                        items = content['items']
                        if markFlag:
                            marks = list(content['marks'])

                    exFrmt = content['format']
                    Frmt = snippets[exFrmt]

                    texBlurb = parseTexEnv(content['blurb'])
                    HdrStr = re.sub('blurb',texBlurb,Frmt['header'])
                    ExStr.append(HdrStr)

                    for item in items:

                        texItem = parseTexEnv(item)

                        QuStr = re.sub('InStr',texItem,Frmt['item'])  # esc '\'
                        if markFlag and not SolutionFlag:
                            MrkStr = '[' + marks.pop(0) +']'
                        else:
                            MrkStr = ''
                        QuStr = re.sub('MrkStr',MrkStr,QuStr)

                        ExStr.extend(pad(QuStr,'\t'))

                    ExStr.append(Frmt['footer'])                # Add footer

                    if SolutionFlag or newPageFlag:

                        ExStr.append('\\newpage\n')   # new page for solutions

                if compendFlag:

                    ExStr.append('\\end{top_enumerate}\n')


                # Deal with randomisation for the exercise
                if 'params' in ex.keys():

                    if 'decimalPlaces' in ex.keys():
                        decMax = int(ex['decimalPlaces'])
                    else:
                        decMax = 3

                    paramDict = {}
                    paramDict = genParams(ex['params'])
                    for label in paramDict.keys():
                        value = paramDict[label]

                        # Set display formatting depending on value
                        # Supports lists and matrices (lists of lists)
                        if isinstance(value,str):
                            StrFrmt = '{:s}'
                        elif isinstance(value,list):
                            listStr = ''
                            StrFrmt = '{:s}'
                            valueList = []
                            for item in value:
                                if isinstance(item, list):
                                    for subitem in item:
                                        if isinstance(subitem, int) or \
                                                subitem.is_integer():
                                            listStr += ' {:d} &'
                                            valueList.append(int(subitem))
                                        else:
                                            dec = decimalCheck(subitem,decMax)
                                            listStr += '{:.' +str(dec)+ 'f} &'
                                            valueList.append(subitem)

                                    listStr = listStr[:-1] + '¬¬\n'

                                elif isinstance(item, int) or \
                                        item.is_integer():
                                    listStr += '{:d},'
                                    valueList.append(int(item))
                                else:
                                    dec = decimalCheck(item,decMax)
                                    listStr += '{:.' + str(dec) + 'f},'
                                    valueList.append(item)

                            listStrFrmt = listStr.format(*valueList)

                            # Put header/footer for matrices and lits
                            if isinstance(value[0], list):
                                value = '¬left( {¬begin{array}{' +\
                                    'c'*len(value) + '}\n' + listStrFrmt +\
                                    '¬end{array} } ¬right)'
                            else:
                                value = '[' + listStrFrmt[:-1] + ']'

                        else:
                            if isinstance(value, int) or value.is_integer():
                                StrFrmt = '{:d}'
                                value = int(value)
                            else:
                                dec = decimalCheck(value,decMax)
                                StrFrmt = '{:.' + str(dec) + 'f}'

                        subStr = StrFrmt.format(value)
                        subStr = re.sub('"','', subStr)
                        if compendFlag:
                            subStr = '{¬bf ' + subStr + '}'
                        else:
                            subStr = '{' + subStr + '}'

                        for i in range(len(ExStr)):

                            # Check for plots, else straight replace
                            if '¬add' in ExStr[i]:

                                plotStr = re.sub('¬bf','',subStr[1:-1])
                                ExStr[i] = re.sub('\{' + label + '\}',
                                                  plotStr,
                                                  ExStr[i])
                            else:

                                ExStr[i] = re.sub('\{' + label + '\}',
                                                  subStr,
                                                  ExStr[i])
                            # Eliminate exponents of power 1
                            ExStr[i] = re.sub('\^\{1\}','', ExStr[i])
                            ExStr[i] = re.sub('\^\{¬bf 1\}','', ExStr[i])

            templateStr = safesub('ExStr_' + str(sectionCount),
                                  "".join(ExStr),
                                  templateStr)
            sectionCount += 1

        # Reverse safe substition of backslash
        templateStr = re.sub('¬','\\\\',templateStr)

        # Write exercises to file
        save_path = os.path.splitext(build_file)[0]
        if not os.path.exists(save_path):
            os.makedirs(save_path,mode=0o777)

        with open(save_path + '/' + outName, 'w') as f_out:
            f_out.write(templateStr)
        f_out.close
        print('  Done, saved to: ' + save_path + '/' + outName + '\n')

        # Compile latex file - Twice to ensure table of contents etc. are OK
        print('  Compiling PDF output - 2 compliation runs required')
        for run in range(2):
            try:
                subprocess.run(['pdflatex',
                                  '-output-directory',
                                  save_path , save_path + '/' + outName ],
                               timeout=30)
            except subprocess.TimeoutExpired:
                print('  Run {:d}'.format(run+1))
                print('  Timeout error: pdflatex seems to be hanging.')
                print('  - Check pdf file is not already open in a reader')
                print('  - Try to compile the .tex file manually to find')
                print('    possible latex syntax errors.')
                pass

        print('  Done\n')

    return None

#------------------------------------------------------------------------------
def build_xml(BankJSON,build_file):

    print('\nBuilding XML file for moodle STACK from build file\n')

    # Load assets
    with open(build_file) as f:        # Load build instructions
        json_str = f.read()
        setup = json.loads(json_str)
    f.close

    with open(BankJSON) as f:          # Load question bank
        json_str = f.read()
        exBank = json.loads(json_str)
    f.close

    # with open('stacktex/snippets.json') as f:          # Load formats
    head, tail = os.path.split(inspect.getsourcefile(import_ex))
    with open(os.path.join(head,'snippets.json')) as f:          # Load formats
        json_str = f.read()
        snippets_all = json.loads(json_str)
        snippets = snippets_all['xml']
    f.close

    #--------------------------------------------------------------------------
    # Pop the meta-data out of the dictionary, configure runs.
    if 'newPage' in setup:
        setup.pop('newPage')             # New page flag irrelevant for XML
    if 'seed' in setup:
        setup.pop('seed')                # Random seed irrelevant for XML

    setup.pop('template')            # Choice of template irrelevant for XML
    template = 'stack.xml'           # Choice of template - FIXED
    exListBase = setup.pop('exList')            # List of exercises from bank
    if 'verbose' in setup:                      # Verbose feedback flag
        verbose = setup.pop('verbose')
        if not isinstance(verbose,bool):        # Must be boolean
            verbose = True
    else:
        verbose = True

    if 'marks' in setup:                    # Include Marks flag
        markFlag = setup.pop('marks')
        if not isinstance(markFlag,bool):   # Must be boolean
            markFlag = False
    else:
        markFlag = False

    filename = setup.pop('filename')            # Chosen file name
    outName = filename + '.xml'

    # Load corresponding template
    # with open('stacktex/templates/' + template) as f:
    with open(os.path.join(head,'templates',template)) as f:
        templateStr = f.read()
    f.close
    #--------------------------------------------------------------------------
    print('  Build file: ' + outName)

    # Replace fields in template by data remaining in the instruction json
    for key in setup.keys():
        templateStr = safesub(key,setup[key],templateStr)

    # Add exercises from list to the exercise string array, with correct format
    ExStr = []
    for exList in exListBase:
        for exLabel in exList:

            print('  Processing {:s}'.format(exLabel))

            # Get raw exercise components from exercise bank
            ex = exBank[exLabel]
            Q_content = ex['questions']
            QPrompts = Q_content['prompts']
            QTypes = Q_content['types']
            S_content = ex['solutions']
            tolerances = S_content['tolerance']
            QStr = snippets['QBase']
            QFrmt = snippets['Qtext']
            funcDict = snippets['CASfuncs']
            if 'decimalPlaces' in ex.keys():
                decMax = int(ex['decimalPlaces'])
            else:
                decMax = 3

            # Initialise temporary working lists
            QText = []
            InStr = []
            SolStrs = []
            SolVars = []
            FdbckStr = []
            xmlPrompts = []

            # If the question is parametrised, generate Stack version
            if 'params' in ex.keys():
                exParams =  ex['params']
                random.seed(0)
                paramDict = genParams(exParams)
                paramList = processParamFuncs(exParams, paramDict, funcDict)
                SolVars = paramList

            # Process main question text, substituting parameter values
            xmlBlurb = xmlParse(Q_content['blurb'])
            xmlBlurbStr = paramSub(xmlBlurb[0], paramDict,decMax)
            HdrStr = re.sub('blurb',xmlBlurbStr,QFrmt['header'])

            for line in HdrStr.splitlines():
                QText.append(line + '\n')

            marks = list(Q_content['marks'])
            ExMark = sum(int(mark) for mark in marks)
            # Display marks in question text if requested
            if markFlag:

                markStrs = [r'&nbsp;&nbsp;&nbsp;&nbsp;\textbf{['+'{:s}'.format(
                    mark) + ']}' for mark in marks]

            # Process questions text
            Qnum = 1
            for item in Q_content['items']:

                # Add question text for item
                if markFlag:
                    item += markStrs.pop(0)
                xmlItem = xmlParse(item)
                xmlItemStr = paramSub(xmlItem[0], paramDict, decMax)
                QuStr = re.sub('QItem',xmlItemStr,QFrmt['item'])
                QuStr = re.sub('Qnum',str(Qnum),QuStr)

                # Add question prompts, saving them for solution
                QPrompt = QPrompts.pop(0)
                xmlPrompt = xmlParse(QPrompt)
                xmlPrompt = paramSub(xmlPrompt[0], paramDict, decMax)
                xmlPrompt = re.sub('<br>','',xmlPrompt)     # Force inline
                xmlPrompt = re.sub('\[','(',xmlPrompt)      # Force inline
                xmlPrompt = re.sub('\]',')',xmlPrompt)      # Force inline
                QuStr = re.sub('QPrompt',xmlPrompt,QuStr)
                xmlPrompts.append(QPrompt)
                QText.extend(QuStr.splitlines())

                Qnum += 1

            # Process inputs and solutions
            Qnum = 1
            fdbckMap = {}
            for item in S_content['items']:

                # Add corresponding input fields
                itemInput = snippets['InputXML']
                itemInput = re.sub('Qnum',str(Qnum),itemInput)
                item = re.sub('\n','',item)     # remove any newlines

                # Check if solution is in parameter dict, use it if so
                if item in paramDict.keys():
                    fdbckMap['sol'+str(Qnum)] = item    # Flag replacement
                    itemInput = re.sub('sol'+str(Qnum),item,itemInput)
                    itemStr = paramSub(r'{'+item+'}',  paramDict, decMax)
                    if itemStr[0] == '[' and itemStr[-1] == ']':
                        itemStr = '$' + itemStr + '$'

                    prompt = xmlPrompts.pop(0)
                    if prompt == '':
                        eqsign = ''
                    else:
                        eqsign = '$=$'
                    SolStr = prompt + eqsign + itemStr
                    SolStrs.append(SolStr)

                    # Adapt input type as required
                    value = paramDict[item]
                    # Boolean
                    if isinstance(value,str):
                        if 'true' in value or 'false' in value:
                            itemInput = re.sub('algebraic','boolean',itemInput)
                    # Matrix
                    elif isinstance(value,list):
                        if isinstance(value[0],list):
                            itemInput = re.sub('algebraic','matrix',itemInput)

                # Else, parse solutions from Latex
                else:
                    # Boolean
                    if 'true' in item.lower() or 'false' in item.lower():
                        symbItem = re.sub('\n','',item.lower())
                        itemInput = re.sub('algebraic','boolean',itemInput)
                    # Matrix
                    elif item[0]=='[' and item[-1]==']':
                        symbItem = 'matrix(' + re.sub('\n','',item) + ')'
                        itemInput = re.sub('algebraic','matrix',itemInput)
                    # Algebraic
                    else:
                        symbcheck = logCheck(item)
                        tokens = symbcheck[1]
                        CASVars = symbcheck[2]
                        symbItem = symbParse(symbcheck[0],
                                             list(paramDict.keys()))
                        if tokens:
                            for token in tokens[0]:
                                symbItem = re.sub(token[0],token[1],symbItem)
                            for var in CASVars:
                                SolVars.append(var)
                                # SolVars.append(var + ';')
                            # SolVars = list(set(SolVars + CASVars))

                    SolVars.append('sol' + str(Qnum) + ':' + symbItem + ';\n')
                    # SolVars.append('sol' + str(Qnum) + ':' + symbItem + '\n')
                    prompt = xmlPrompts.pop(0)
                    if prompt == '':
                        eqsign = ''
                    else:
                        eqsign = '='
                    SolStr = re.sub('\$','',prompt + eqsign + item)
                    SolStrs.append('$'+SolStr+'$')

                for line in itemInput.splitlines():
                    InStr.append(line + '\n')

                Qnum += 1

            # Feedback: Use feedback if available, bare solutions otherwise
            # HERE is where we insert the short vs. long feedback
            if 'feedback' in S_content and verbose == True:
                FdBck = S_content['feedback']
            else:
                FdBck = SolStrs

            Qnum = 1
            for item in FdBck:

                itemFdbck = snippets['FeedbackXML']

                xmlItem = xmlParse(item)
                itemFdbckStr = paramSub(xmlItem[0], paramDict, decMax)
                itemFdbck = re.sub('FeedText',itemFdbckStr,itemFdbck)
                itemFdbck = re.sub('FeedVars',xmlItem[1],itemFdbck)
                itemFdbck = re.sub('Qnum',str(Qnum),itemFdbck)
                itemFdbck = re.sub('QMark',marks.pop(0),itemFdbck)

                # Check if solution variable already exists, substitute if so
                if 'sol'+str(Qnum) in fdbckMap.keys():
                    itemFdbck = re.sub('sol'+str(Qnum),
                                       fdbckMap['sol'+str(Qnum)],
                                       itemFdbck)

                # Modify test setting according to question type if required
                testType = QTypes.pop(0)
                tolerance = tolerances.pop(0)
                if testType.lower() == 'numerical':
                    itemFdbck = re.sub('testType','NumAbsolute',itemFdbck)
                    # If no tolerance is specified, set to default
                    if tolerance == '':
                        strFrmt = '{:.' + str(decMax+1) + 'f}'
                        tol = strFrmt.format(0.5*10**(-decMax))
                    else:
                        tol = tolerance
                    itemFdbck = re.sub('testTol',tol,itemFdbck)
                elif testType.lower() == 'algebraicexact':
                    itemFdbck = re.sub('testType','EqualComAss',itemFdbck)
                    itemFdbck = re.sub('testTol','',itemFdbck)
                else:
                    itemFdbck = re.sub('testType','AlgEquiv',itemFdbck)
                    itemFdbck = re.sub('testTol','',itemFdbck)

                # Append feedback
                for line in itemFdbck.splitlines():
                    FdbckStr.append(line + '\n')

                Qnum += 1

            QText.append(QFrmt['footer'])                     # Add list footer

            # Replace fields in template
            QStr = safesub('ExTitle',exLabel,QStr)
            QStr = re.sub('QText',"".join(QText),QStr)
            QStr = re.sub('ExMark',str(ExMark),QStr)
            QStr = re.sub('QVars',"".join(SolVars),QStr)
            QStr = re.sub('InputXML',"".join(InStr),QStr)
            QStr = re.sub('FeedbackXML',"".join(FdbckStr),QStr)

            ExStr.append(QStr)


    templateStr = re.sub('ExStr',"".join(ExStr),templateStr)

    # Reverse safe substition of backslash
    templateStr = re.sub('¬','\\\\',templateStr)

    # Write exercises to file
    save_path = os.path.splitext(build_file)[0]
    if not os.path.exists(save_path):
        os.makedirs(save_path,mode=0o777)

    with open(save_path + '/' + outName, 'w') as f_out:
        f_out.write(templateStr)
    f_out.close
    print('  Done, saved to: ' + save_path + '/' + outName + '\n')
    return None

#------------------------------------------------------------------------------
