# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 15:24:38 2020

@author: Sylvain
"""

import re
import copy
import string
import random
import numpy as np
from scipy.stats import norm, binom
from sympy.parsing.latex import parse_latex

#------------------------------------------------------------------------------
def decimalCheck(value,decMax):
    """
    # Check minimum number of decimal values required

    Parameters
    ----------
    value : TYPE
        DESCRIPTION.
    decMax : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """

    for dec in range(decMax):
        value *=10
        # if value.is_integer():
        if value.is_integer() or abs(value - int(value)) < 1e-4:
            return dec+1

    return decMax
#------------------------------------------------------------------------------
def genParams(paramStr):
    """
    Generate parameter dictionary from instruction set

    Parameters
    ----------
    paramStr : TYPE
        DESCRIPTION.

    Returns
    -------
    paramDict : TYPE
        DESCRIPTION.

    """

    paramDict = {}
    params = paramStr.splitlines()
    for param in params:

        if not param == '':

            paramInfo = re.split(':',param)
            label = paramInfo[0]
            valuebase = paramInfo[1]

            for key in paramDict.keys():
                valuebase = re.sub(key,str(paramDict[key]),valuebase)

            # value = safeEval(valuebase)

            if label[0] == '[':             # Multiple assignment

                labelItems = re.split(',', re.sub('[\[\] \s ]','',label))
                # valueItems= re.split(',', re.sub('[\[\] \s ]','',valuebase))
                valuebase = valuebase[
                    valuebase.find('[')+1:valuebase.rfind(']')]
                # valueItems = re.split(',(?!.*\))', valuebase)
                valueItems = re.split(',(?![^\(]*\))', valuebase)


                # if len(labelItems) != len(value):
                if len(labelItems) != len(valueItems):
                    print("Number of multiple assignments does not match")
                    print(param)

                else:
                    for item in labelItems:
                        # paramDict[item] = value.pop(0)
                        paramDict[item] = safeEval(valueItems.pop(0))

            else:                           # Normal assignment

                # paramDict[label] = value
                paramDict[label] = safeEval(valuebase)

    return paramDict
#------------------------------------------------------------------------------
def get_fieldName(line):
    """ Extracts fieldname from the field instruction line

    Parameters
    ----------
    line : string
        Line containing the new field instruction in curly brackets

    Returns
    -------
    substring with the fieldname.

    """
    return re.findall(r'\{(.*?)\}',line)[0]
#------------------------------------------------------------------------------
def logCheck(item):
    """ Logarithm substitution for STACK translation
        Designed to deal with the fact that MAXIMA only has the natural
        logarithm, therefore requiring specific definitions for other logs

    Parameters
    ----------
    item : String containing LaTeX maths expression
        DESCRIPTION.

    Returns
    -------
    list :
        item : input LaTeX string with logarithms substituted.
        CASVars: List of new logarithm definitions
        tokens: tokens for logarithm substitution

    """

    funcs = ['ln','log_e', 'log_2', 'log_10']
    subs = ['ln','ln','ln','ln']
    tokenlist = [
                [['log\(','log('],[', E\)',')']],
                [['log\(','log_e('],[', E\)',')']],
                [['log\(','log_2('],[', E\)',')']],
                [['log\(','log_10('],[', E\)',')']]
                ]
    varlist =['',
              'log_e(x) := log(x);\n',
              'log_2(x) := log(x) / log(2);\n',
              'log_10(x) := log(x) / log(10);\n']
    count = 0
    CASVars = []
    tokens = []

    for func in funcs:

        if func in item:
            item = re.sub(func,subs[count],item)
            CASVars.append(varlist[count])
            tokens.append(tokenlist[count])

        count += 1

    return [item,tokens,CASVars]
#------------------------------------------------------------------------------
def parseTex(item):

    OutStr = []

    for line in item.splitlines():

        # substitute '¬' for '\' regex operations
        safeline = re.sub('\\\\','¬',line)
        OutStr.append(safeline + '\n')

    return "".join(OutStr)
#------------------------------------------------------------------------------
def parseTexEnv(item):      # COMBINE IN FUTURE

    OutStr = []

    for line in item.splitlines():

        # substitute '¬' for '\' regex operations
        safeline = re.sub('\\\\','¬',line)

        # Plot management. Simply encapsulates '{tikzpicture}' in a 'center'
        if 'begin{tikzpicture}' in line:
            safeline = '¬begin{center}\n'+safeline

        if 'end{tikzpicture}' in line:
            safeline = safeline + '\n¬end{center}'

        # Table management. Simply encapsulates 'tabular' in a 'center'
        if 'begin{tabular}' in line:
            safeline = '¬begin{center}\n'+safeline

        if 'end{tabular}' in line:
            safeline = safeline + '\n¬end{center}'

        # if flag:
            # OutStr.append(safeline + '\n')
        OutStr.append(safeline + '\n')

    return "".join(OutStr)
#------------------------------------------------------------------------------
def processParamFuncs(exParams,paramDict,funcDict):
    """
    Process the exercise parameters into CAS compatible definitions

    Parameters
    ----------
    exParams : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    funcList = []
    funcIncluded = []
    paramList = ['\n/* Exercise parameters */\n']

    paramLines = exParams.splitlines()
    for line in paramLines:

        # Indentify any required supplementary functions
        for func in funcDict.keys():
            if func in line and func not in funcIncluded:
                if funcList == []:
                      funcList.append('/* Extra function definitions'+\
                                      ' for Maxima */\n')
                funcList.append(funcDict[func])
                funcIncluded.append(func)

        # Format conversion checks
        if not line == '':

            paramInfo = re.split(':',line)
            label = paramInfo[0]
            valuebase = paramInfo[1]

            # Check for a nested list => matrix variable
            if '[[' in line and ']]' in valuebase:
                valuebase = re.sub('\[\[','matrix([',valuebase)
                valuebase = re.sub('\]\]','])',valuebase)
                line = label + ':' + valuebase

            # Check for floats, override rational behaviour
            # Find decimal places based on sample value

            if label[0] == '[':             # Multiple assignment
            # elif valuebase.strip()[0] == '[':         # Multiple assignment

                labelItems = re.split(',', re.sub('[\[\] \s ]','',label))
                # variables =  re.split(',', re.sub('[\[\] \s ]','',valuebase))
                valueCheck = valuebase[
                    valuebase.find('[')+1:valuebase.rfind(']')]
                # variables = re.split(',(?!.*\))', valuebase)
                variables = re.split(',(?![^\(]*\))', valueCheck)

                for item in labelItems:
                    value = paramDict[item]
                    var = variables.pop(0)
                    if isinstance(value, float) and not value.is_integer():
                        valuebase = valuebase.replace(var,
                                                  "float({:s})".format(var))
                        # valuebase = re.sub(var,
                        #                    "float({:s})".format(var),
                        #                     valuebase)

                line = label + ':' + valuebase

            else:                           # Normal assignment

                value = paramDict[label]
                if isinstance(value, float) and not value.is_integer():
                    line = label + ':' "float({:s})".format(valuebase)

            # Check for conditional variable definition
            if 'if' in line and 'then' in line and 'else' in line:

                condInfo = re.search('if(.*)then(.*)else(.*)', line)
                if condInfo:
                    cond = re.sub(' ','',condInfo.group(1))
                    cond = 'if is(' + re.sub('==','=',cond) + ')'

                    valIfTrue = re.sub(' ','',condInfo.group(2))
                    valIfTrue = ' then ' + label + ':' + valIfTrue

                    valIfFalse = re.sub(' ','',condInfo.group(3))
                    valIfFalse = ' else ' + label + ':' + valIfFalse

                    line = cond + valIfTrue + valIfFalse

            line += ';' # Fix semi colon missing

        paramList.append(line + '\n')


    outList = funcList + paramList

    return outList
#------------------------------------------------------------------------------
def paramSub(textStr,paramDict,decMax):
    """
    Substitute latex parameter display instructions for STACK instructions

    Parameters
    ----------
    textStr : TYPE
        DESCRIPTION.
    paramDict : TYPE
        DESCRIPTION.
    decMax : TYPE
        DESCRIPTION.

    Returns
    -------
    textStr : TYPE
        DESCRIPTION.

    """

    for param in paramDict.keys():
        if '{'+param+'}' in textStr:

            # Find decimal places based on sample value
            value = paramDict[param]
            if isinstance(value, list):
                if isinstance(value[0], list):
                    items = [item for sublist in value for item in sublist]
                else:
                    items = value

                if all(isinstance(item, int) or item.is_integer()
                       for item in items):
                    token = '{@' + param + '@}'
                else:
                    # decList = 0
                    # for item in items:
                    #     if not (isinstance(item, int) or item.is_integer()):
                    #         decList = max([decimalCheck(item,decMax),decList])
                    # token = '{@decimalplaces(' + param + ',' + str(decList) + ')@}'
                    token = '{@decimalplaces(' + param + ',' + str(decMax) + ')@}'
            elif isinstance(value, str) :
                token = '{@' + param + '@}'
            elif isinstance(value, int) or value.is_integer():
                token = '{@' + param + '@}'
            else:
                # dec = decimalCheck(value,decMax)
                # token= '{@decimalplaces(' + param + ',' + str(dec) + ')@}'
                # dec = decimalCheck(value,decMax)
                token= '{@decimalplaces(' + param + ',' + str(decMax) + ')@}'

            # substitute
            textStr = re.sub(r'{'+param+'}',token,textStr)

    return textStr

#------------------------------------------------------------------------------
def safeEval(line):
    """
    Generate parameter values with a safe evaluation of the instructions

    Parameters
    ----------
    line : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    # Auxiliary function to return location of a match in string
    def location(e):
        return e['loc']

    funcDict = {'binom_pdf':'binom.pmf',
                'norm_qnt':'norm.ppf',
                'norm_cdf':'norm.cdf',
                'norm_pdf':'norm.pdf',
                'abs':'np.abs',
                'ceiling':'np.ceil',
                'floor':'np.floor',
                'ln':'np.log',
                'log_2':'np.log2',
                'log_10':'np.log10',
                'sqrt':'np.sqrt',
                'round':'np.round',
                'median':'np.median'}

    #--------------------------------------------------------------------------
#    for func in funcDict.keys():
#        if func in line:
#            matches = re.findall(func+r'\((.*?)\)',line)
#            for match in matches:
#                funcVal = eval(funcDict[func]+'(' + match + ')')
#                line = re.sub(func+'\(' + match + '\)',str(funcVal),line)
    #--------------------------------------------------------------------------
    # Evaluate value of any special functions
    if any(func in line for func in funcDict.keys()):
        funcList = []
        for func in funcDict.keys():
            if func in line:
                match = re.search(func,line)
                funcList.append({'func': func, 'loc':match.span()[0]})

        funcList.sort(reverse=True, key=location)

        for funcItem in funcList:
            func = funcItem['func']
            matches = re.findall(func+r'\((.*?)\)',line)
            for match in matches:
                matchPyExp = re.sub('\^','**', match)
                funcVal = eval(funcDict[func]+'(' + matchPyExp + ')')
#                line = re.sub(func+'\(' + match + '\)',str(funcVal),line)
                line = line.replace(func+'(' + match + ')',str(funcVal))

    # Pick value from list.
    # Code below manages python 0 indexing vs maxima 1 indexing
    if '[' in line and ']' in line and '][' in line:
        line = line.replace(']','-1]')
        line = line.replace('-1][','][')

    # Evaluate boolean from condition
    if 'if' in line and 'then' in line and 'else' in line:

        condInfo = re.search('if(.*)then(.*)else(.*)', line)
        if condInfo:
            cond = re.sub(' ','',condInfo.group(1))
            if '"' in condInfo.group(2):
                valIfTrue = condInfo.group(2)
            else:
                valIfTrue = re.sub(' ','',condInfo.group(2))

            if '"' in condInfo.group(3):
                valIfFalse = condInfo.group(3)
            else:
                valIfFalse = re.sub(' ','',condInfo.group(3))

            if re.search('[a-zA-Z]', cond) is None:

                if eval(cond):
                    return valIfTrue
                else:
                    return valIfFalse

            else:
                print("Conditional statement contains characters")
                print(cond)
                return None

        else:
            print("Conditional statement incorrectly formatted")
            print(cond)
            return None

    # Evaluate from random selection
    if 'rand' in line:

        matches = re.findall(r'rand\((.*?)\)',line)

        for match in matches:

            if '[' in match and ']' in match:
                rndval = eval('random.choice('+match+')')
                match = re.sub('\[','\[',match)
                match = re.sub('\]','\]',match)
            else:
                rndval = random.randrange(int(match))

            line = re.sub('rand\(' + match + '\)',str(rndval),line)

    line = re.sub('\^','**', line)

    if re.search('[a-zA-Z]', line) is None:
        return eval(line)
    else:
        print("Variable definition incorrectly formatted")
        print(line)
        return None
#------------------------------------------------------------------------------
def safesub(pttrn, repl, InStr):

    safeRepl = re.sub('\\\\','¬',repl)
    OutStr = re.sub(pttrn,safeRepl,InStr)

    return OutStr
#------------------------------------------------------------------------------
def sorted_nicely( l ):
    """ Sorts the given iterable in the way that is expected.

    Parameters
    ----------
    l -- The iterable to be sorted.

    Returns
    -------
    sorted iterable

    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key = alphanum_key)
#------------------------------------------------------------------------------
def symbParse(item,paramNames):
    """ Symbolic parse of LaTeX maths to CAS, with named parameters

    Parameters
    ----------
    item : String containing LaTeX maths expression

    Returns
    -------
    symbStr : string containing STACK-compatible expression

    """
    # tokenList = list(string.ascii_uppercase) + list(string.ascii_lowercase)
    # tokenDict = {}
    # item = re.sub('\$','',item)            # remove dollars

    item = re.sub('\$','',item)            # remove dollars
    tokenListFull = list(string.ascii_uppercase) + list(string.ascii_lowercase)
    # tokenList = set(tokenListFull)-set(item)    # Only use tokens not in 'item'
    tokenListBase = set(tokenListFull)-set(item)    # Only use tokens not in 'item'
    tokenList = copy.deepcopy(tokenListBase)
    tokenDict = {}

    for run in range(2):
        itemRun = copy.deepcopy(item)

        for paramName in paramNames:
            if paramName in itemRun:
                if run==0:
                    # Remove named parameters to identify regular variables
                    itemRun = re.sub(paramName,'1',itemRun)
                else:
                    # Substitute named parameter by safe token
                    token = tokenList.pop()
                    itemRun = re.sub(paramName,token,itemRun)
                    tokenDict[token] = paramName

        symb = parse_latex(itemRun)
        symbStr = str(symb)

        # After 1st run, remove variables from list of potential tokens
        if run == 0:
            # for token in tokenList:
            for token in tokenListBase:
                if token in symbStr:
                    tokenList.remove(token)

    # Reverse parameter substitution if tokens have been used
    if not tokenDict == {}:
        for token in tokenDict.keys():
            symbStr = re.sub(token,tokenDict[token],symbStr)

    # Clean up symbolic string for maxima syntax
    symbStr = re.sub('\*\*','^', symbStr)                   # swap ** -> ^
    symbStr = re.sub(r'([a-zA-Z0-9])(\()',r'\1*\2',symbStr) # x(foo) -> x*(foo)
    funlist = ['log']
    for fun in funlist:
        symbStr = symbStr.replace(fun+'*',fun)

    return symbStr
#------------------------------------------------------------------------------
def pad(InStr,PadStr):

    lines = InStr.splitlines()
    padLines = []
    for line in lines:
        padLines.append(PadStr+line+'\n')

    return padLines
#------------------------------------------------------------------------------
def trim(line):
    """ Trims line breaks from wokring string

    Parameters
    ----------
    line : string
        working string to be appended to field

    Returns
    -------
    line : string
        working string with leading/trailing line breaks removed
    """
    while len(line) > 0 and line[0] == '\n':
        line = line[1:]

    while len(line) > 0 and line[-1] == '\n':
        line = line[:-1]

    return line
#------------------------------------------------------------------------------
def xmlParse(item):
    """ Parse LaTeX text into STACK XML-compatible standard

    Parameters
    ----------
    item : String containing LaTeX markup and environments

    Returns
    -------
    list : containing STACK-XML text.
        - xmlStr: XML string corresponding to LaTeX input
        - varStr: string of STACK variables

    """
    xmlStr = []
    varStr = []
    dlrCount = 0
    flag = True
    axisTokens = ['xmin',
                  'xmax',
                  'ymin',
                  'ymax']

    for line in item.splitlines():

        # Substitute '\' for '¬' ensuring safe regex operations
        safeline = re.sub('\\\\','¬',line)

        # Substitute escaped % symbols from latex. {\%} is for Maths %
        safeline = re.sub('¬%','%',safeline)
        safeline = re.sub('\{%\}','¬%',safeline)

        # Replace '>' and '<' signs to avoid breaking xml - Step 1
        # Replace '<' by '&lt' in 2 steps (avoid reserved & in tabular)
        safeline = re.sub('<','¬lt',safeline)   # Protect < as less than
        safeline = re.sub('>','¬gt',safeline)   # Protect > as greater than

        # Replace Bold/Italic environments
        texTokens = ['¬textbf{','¬emph{']
        xmlTokens = [['<b>','</b>'],['<i>','</i>']]
        for token in texTokens:
            xmlToken = xmlTokens.pop(0)
            if re.search(token,safeline):
                matches = re.split(token,safeline)
                count = 0
                Nmatch = len(matches)
                outstr = ''
                for match in matches:

                    if count < Nmatch-1:
                        match += xmlToken[0]

                    if count > 0:
                        brktCount = 1
                        for i in range(len(match)):
                            if match[i] == '{':
                                brktCount += 1
                            elif match[i] == '}':
                                brktCount -= 1
                            if brktCount == 0:
                                match = match[0:i] + xmlToken[1] + match[i+1:]
                                break

                    outstr += match
                    count += 1

                safeline = outstr

        # Replace skips
        safeline =  re.sub('¬([a-z]*)skip','<br>',safeline)

        # Replace $ Math delimiters for STACK
        # Replace protected dollars (protected '\$' currency)
        safeline = re.sub('¬\$','¬DLR¬',safeline)   # Protect $ money

        # Look for inline $ pairs -> equations in same line
        match = re.search('\$.*\$',safeline)
        if match:

            if match.start() == 0 and match.end() == len(safeline):
                cas_dlr = ['¬[','¬]']
            else:
                cas_dlr = ['¬(','¬)']

            matches = re.split('\$',safeline)
            count = 0
            Nmatch = len(matches)
            outstr = ''
            for match in matches:

                if count < Nmatch-1:
                    match += cas_dlr[count % 2]

                outstr += match
                count += 1

            safeline = outstr

        # Look for multiline $ pairs -> equations split over lines, use \[,\]
        multimatch = re.search('\$',safeline)
        if multimatch:
            if dlrCount % 2 == 0:
                safeline = re.sub('\$','¬[',safeline)
                dlrCount += 1
            else:
                safeline = re.sub('\$','¬]',safeline)
                dlrCount += 1

        safeline = re.sub('¬DLR¬','¬$',safeline)

        # Table management. Build HTML table from instructions
        if 'begin{tabular}' in line:
            hdSty = '<th style="padding-left:10px;padding-right:10px;">'
            hdEnd = '</th>\n'
            rwSty = '<td style="padding-left:10px;padding-right:10px;">'
            rwEnd = '</td>\n'
            flag = False

            tabStr = ''
            tabLine = '<table style="text-align: center">\n    <tbody>\n'

            tabHeader = True

        if not flag and '&' in line and '¬¬' in safeline:
            tabLine = re.sub('HLINE','',tabLine)
            tabStr += tabLine
            tabLine = ''

            if tabHeader == True:
                lineSty = '            ' + hdSty
                lineEnd = hdEnd
                tabHeader = False
            elif tabHeader == False:
                lineSty = '            ' + rwSty
                lineEnd = rwEnd

            matches = re.split('&',safeline)
            tabLine = '        <tr HLINE>\n'
            for match in matches:
                tabLine += lineSty + re.sub('¬¬','',match) + lineEnd
            tabLine += '        </tr>\n'

        elif 'hline' in line:
            hlineStr = "style=border-bottom:1px solid black"
            tabLine = re.sub('HLINE',hlineStr,tabLine)
            tabStr += tabLine
            tabLine = ''

        if 'end{tabular}' in line:
            tabStr += tabLine + '    </tbody>\n</table>'
            flag = True
            safeline = tabStr

        # Plot management. Build maxima plot from pgfplot instructions
        if 'begin{tikzpicture}' in line:
            flag = False
            pointColors = ['black',
                           'blue',
                           'red',
                           'green',
                           'magenta',
                           'cyan',
                           'yellow',
                           'orange',
                           'violet',
                           'brown',
                           'gray']

            plotStr = '<p>{@plot([pltList], [domain], [range], st, col, '+\
                    '[point_type, bullet], [box, false], [axes, solid], '+\
                    '[xtics, xMin, step, xMax], leg)@}</p>'
            pltlist = ''
            st = ''
            col = ''
            leg = ''
            countFn=0
            countPt=0
            xMin = ''
            xMax = ''
            yMin = ''
            yMax = ''

        if not flag and any(token in line for token in axisTokens):
            safeline = re.sub('[ ,=]','',safeline)
            if 'xmin' in safeline:
                xMin = re.sub('xmin','',safeline)
            elif 'xmax' in safeline:
                xMax = re.sub('xmax','',safeline)
            elif 'ymin' in safeline:
                yMin = re.sub('ymin','',safeline)
            elif 'ymax' in safeline:
                yMax = re.sub('ymax','',safeline)

        if 'addplot' in line:

            if 'coordinates' in line:
                mrkInfo = re.findall('\[.*\]',safeline)
                pltMrk = re.sub(r"([\[\]])",'',mrkInfo[0])

                if 'addplot+' in line:
                    pltInfo = re.findall('{.*}',safeline)
                    pltStr = re.sub(r"([ {}}])",'',pltInfo[0])
                    Pts = re.split('\)\(',pltStr)
                    if 'only marks' in line:
                        # plot a scatterplot
                        for Pt in Pts:
                            Pt = re.sub('\(','',Pt)
                            Pt = re.sub('\)','',Pt)
                            PtStr = re.sub('X',Pt,'[discrete,[ [X] ]]')
                            varStr.append(
                                'pt' + str(countPt)  + ':' + PtStr + ';\n')
                            pltlist += 'pt' + str(countPt) + ','
                            st += 'points,'
                            col += 'black,'
                            leg += '"Pt ' + str(countPt+1) + '",'
                            countPt+=1

                    else:
                        # plot a Histogram
                        xLag = '0'
                        histStr = ''
                        for Pt in Pts:
                            Pt = re.sub('\(','',Pt)
                            Pt = re.sub('\)','',Pt)
                            X = re.split(',',Pt)
                            tag ='['+X[0]+','+xLag+'],['+\
                                X[0]+',0],['+X[0]+','+X[1]+']'
                            if histStr == '':
                                histStr += tag
                            else:
                                histStr += ',' + tag
                            xLag = X[1]

                        varStr.append('fn' + str(countFn)  + ':' + \
                                      re.sub('X',histStr,
                                             '[discrete,[ X ]]')+';\n')
                        pltlist += 'fn' + str(countFn) + ','
                        st += 'lines,'
                        col += 'blue,'
                        countFn+=1

                else:
                    pltInfo = re.findall('{(.*)}',safeline)
                    if len(re.findall(',',pltInfo[0])) == 1:
                        # plot a point
                        pltStr = re.sub(r"([ {()}}])",'',pltInfo[0])
                        PtStr = re.sub('X',pltStr,'[discrete,[ [X] ]]')
                        varStr.append(
                            'pt' + str(countPt)  + ':' + PtStr + ';\n')
                        pltlist += 'pt' + str(countPt) + ','
                        st += 'points,'
                        # col += 'black,'
                        col += pointColors.pop(0) + ','
                        countPt+=1

                    else:
                        # plot a line
                        pltStr = re.sub(r"([ {}}])",'',pltInfo[0])
                        lineStr = re.sub('\(','[',pltStr)
                        lineStr = re.sub('\)','],',lineStr)
                        for frmtInfo in re.split(',', pltMrk):
                            if 'color=' in frmtInfo:
                                frmtCol = re.sub('color=','',frmtInfo)
                        varStr.append('fn' + str(countFn)  + ':' + \
                                      re.sub('X',
                                             lineStr[:-1],
                                             '[discrete,[ X ]]') + ';\n')
                        pltlist += 'fn' + str(countFn) + ','
                        st += 'lines,'
                        col += frmtCol + ','
                        countFn+=1

            elif 'domain' in line:
                # plot a function
                pltInfo = re.findall('{.*}',line)
                matches = re.split(r"([ ,\[\]])",
                                   re.findall('\[.*\]',line)[0])

                for match in matches:
                    if 'color' in match:
                        color = re.sub(r" ",'',match)
                    if 'domain' in match and len(xMin) == 0:
                        xInfo = re.split(':',re.sub('domain=','',match))
                        xMin = xInfo[0]
                        xMax = xInfo[1]

                pltStr = re.sub(r"([ {}])",'',pltInfo[0])
                varStr.append('fn'+str(countFn) + ':' + pltStr + ';\n')
                pltlist += 'fn' + str(countFn) + ','
                col += re.sub('color=','',color) + ','
                st += 'lines,'
                countFn+=1

        if 'addlegendentry' in line:
            legLine = re.findall('{.*}',safeline)
            legInfo = legLine[0][1:-1]
            legInfo = re.sub('¬\(','',legInfo)
            legInfo = re.sub('¬\)','',legInfo)
            leg += '"' + legInfo + '",'


        if 'end{tikzpicture}' in line:
            flag = True
            varStr.append('st:[style,' + st[0:-1] + '];\n')
            varStr.append('col:[color,' + col[0:-1] + '];\n')
            if leg == '':
                varStr.append('leg:[legend,true];')
            else:
                varStr.append('leg:[legend,'+ leg[0:-1] +'];')

            domain = 'x, ' + xMin + ',' + xMax
            if not yMin == '':
                yRange = 'y, ' + yMin + ',' + yMax
            else:
                yRange = ''
            domain_range = float(xMax) - float(xMin)
            steps = [0.5, 1, 5, 10, 20, 25, 50, 100]
            incr = 0
            while domain_range/steps[incr] > 20:
                incr += 1
            step = steps[incr]

            plotStr = re.sub('pltList',pltlist[0:-1],plotStr)
            plotStr = re.sub('domain',domain,plotStr)
            plotStr = re.sub('xMin',xMin,plotStr)
            plotStr = re.sub('step',str(step),plotStr)
            plotStr = re.sub('xMax',xMax,plotStr)

            if len(yRange) > 0:
                plotStr = re.sub('range',yRange,plotStr)
            else:
                plotStr = re.sub('\[range\], ','',plotStr)

            safeline = plotStr

        # Replace '>' and '<' signs to avoid breaking xml - Step 2
        # Replace '<' by '&lt' in 2 steps (avoid reserved & in tabular)
        safeline = re.sub('¬lt','&lt',safeline)   # Protect < as less than
        safeline = re.sub('¬gt','&gt',safeline)   # Protect > as greater than

        if flag:
            xmlStr.append(safeline + '<br>')

    return ["".join(xmlStr),"".join(varStr)]
