# stackTex

Build and manage STACK Moodle question banks from Latex templates

#### Table of contents
- [Contents and requirements](#contents-and-requirements)
- [Toolkit workflow](#toolkit-workflow)
- [LaTex exercise formatting](#latex-exercise-formatting)
  - [Including tables and figures](#including-tables-and-figures)
  - [Exercise randomisation](#exercise-randomisation)  
  - [Exercise template fields and options](#exercise-template-fields-and-options)
  - [Exercise-level options](#exercise-level-options)
  - [Question-level options](#question-level-options)
- [Setting up a build file](#setting-up-a-build-file)
  - [Available output templates](#available-output-templates)
  - [Build file fields and options](#build-file-fields-and-options)
  - [Common fields, required for all output templates](#common-fields,-required-for-all-output-templates)
  - [Fields specific to the seminar.tex output template](#fields-specific-to-the-seminar.tex-output-template)
  - [Fields specific to the test.tex output template](#fields-specific-to-the-test.tex-output-template)
- [Adding and editing templates](#adding-and-editing-templates)

## Contents and requirements

The contents of the GitHub repository is as follows. Note that in the interest of space, the contents of the `./demo/` subfolder, which provides a demonstration of the toolkit on a sample of exercises, is provided in the `demo_workflow.py` file.

```
stacktex/
├── __init__.py
├── LICENSE
├── requirements.txt
├── demo_workflow.py
├── toolkit.py
├── dependencies.py
├── snippets.json
├── README.md
├── demo/
│   └── contents described in 'demo_workflow.py'
├── latex_exercise_template/
│   ├── tex_template.pdf
│   └── tex_template.pdf
└── templates/
    ├── compendium.tex
    ├── seminar.tex
    ├── stack.xml
    └── test.tex
```

The stackTex toolkit requires the following packages:

```
numpy
scipy
sympy
antlr4-python3-runtime=4.11
```

`numpy` and `scipy` are standard imports for numerical python applications. The `sympy` package forms the core of the toolkit, as it required to parse latex maths expressions and return a string that can be passed to the STACK engine. In turn, this requires a compatible version of the `antlr4` parser.

## Toolkit workflow

The `demo_workflow.py` script provides a example of how to use the toolkit in practice. The top-level functionality is designed to be as user-friendly as possible. Given a path `TexFolder` to a folder containing [raw latex exercises](#latex-exercise-formatting) and a path to a file `BankJSON` which will store the question bank in JSON format, the raw exercises can be imported as follows:

```python
import stacktex.toolkit as st

st.import_ex(TexFolder, BankJSON)
```

Once the exercise bank has been imported, quizzes can be constructed using [build files](#setting-up-a-build-file), which provide a list of exercises to extract from the question bank and a set of options for configuring the output. The same build file can be used to generate a pdf or an XML file that can be imported into Moodle. Given a path to a build file `buildFile`, this is done as follows:

```python
# Use the build file to generate a PDF output
st.build_tex(BankJSON, buildFile)

# Use the build file to generate a Moodle XML file containing STACK questions
st.build_xml(BankJSON, buildFile)
```

It is advisable to use build a [compendium](#available-output-templates), which references the full contents of a question bank in PDF format, as this will facilitate the process of selecting exercises to be included in individual quizzes or worksheets.

## LaTex exercise formatting

This section details the various options that can be set in the raw LaTex exercises to be imported into a question bank, and also documents the features of the toolkit itself.

- The base template is provided in the `/latex_exercise_template` folder.
- The `/demo` folder contains a set of examples written using the template that illustrate the formatting options listed below.

The body of the exercise questions and feedback can use standard LaTeX formatting for maths environments, in particular `$ ... $` and `\[ ... \]` for inline and display maths respectively. Maths formatting environment such as `aligned`, `array`, etc. are supported within these maths environments. An important restriction, however, is that the `\begin{equation} ... \end{equation}` maths environment is not supported for displaying maths. Comments using the `%` symbol are also allowed.

### Including tables and figures

Tables can be included in an exercise using the standard `tabular` environment. Similar to the `\begin{equation} ... \end{equation}` mentioned above, the toolkit will not recognise the `\begin{table} ... \end{table}` environment.
- The `demo/raw_latex_exercises/statistics/descriptive.tex` exercise provides an example of how to include a table in an exercise.

Figures can be included in an exercise using the `pgfplot` package combined with a `\begin{tikzpicture} ... \end{tikzpicture}` environment. As for the maths and table environments, the toolkit does not support the high-level `\begin{figure} ... \end{figure}` environment. Note, it is advisable to only include one plot/figure by exercise, as some MAXIMA installations will experience race conditions when generating multiple plots in a Moodle STACK quiz, resulting in the plots being duplicated or displayed in the wrong order.

The following exercises provide examples of how to include a figure in either the question text or as part of the exercise feedback:
- `demo/raw_latex_exercises/algebra/linear_slope.tex`
- `demo/raw_latex_exercises/algebra/system_of equations.tex`
- `demo/raw latex exercises/statistics/hypothesis.tex`

### Exercise randomisation

A key feature of the stackTex toolkit is the ability to randomise the parameters and solutions of any exercise. This enables the user to:
- Change the solutions of exercises from existing PDF documents (e.g. past tests), allowing re-use of exercises, simply by changing the seed of a random number generator.
- Generate STACK quizzes for a cohort of students where each student gets a unique set of parametrisations and solutions, minimising the risk of students sharing solutions.

This is achieved by declaring the exercise solutions and the parameter values used in an exercise as a set of variables calculated from random draws, and modifying the latex syntax to display the underlying variable values instead of fixed parameters. The exercises in the `demo/raw latex exercises/` folder are provided as a way of illustrating how this can be carried out.

#### Basic parameter declaration rules

Should one wish to randomise an exercise, the all the parameters and variables that require randomisation need to be declared in the `\fieldname{exerciseParameters}` section of the LaTeX template (see [here](#exercise-template-fields-and-options)).

The general syntax for parameter declaration is:
```
pName:expression
```
where `pName` is the name of the variable and `expression` is the expression generating the value of the parameter. Multiple assignment is possible in compact form using:
```
[p1, p2, ...]:[expression1, expression2, ...]
```
So that `expression1` defines `p1`, `expression2` defines `p2` and so forth.

Due to the way the LaTeX input is parsed, **a key rule** that must be followed when picking parameter names is that all parameter names bust be unique strings, such that no parameter name is a substring of another parameter. For example, `p1,p2,p3, ... p9` forms an acceptable list of parameter names, but adding a 10th parameter `p10` is not possible as `p1`, already in the list, is a substring of `p10`.

The right-hand-side `expression` which defines the parameter can be a mathematical expression written using normal mathematical operation syntax `+`, `-`, `*`, `/`, `^`, `()`, combined with maths base functions such as `round`, `abs`, `ceiling`, `floor`, `sqrt`, `ln`, `log_2`, `log_10`, etc. For statistics exercises, the system also supports the binomial pdf `binom_pdf`, the standard normal CDF `norm_cdf` and the standard normal quantile function `norm_qnt`.

The only randomiser available is `rand(N)` which for integer $N$ uniformly draws an integer in the inclusive $[0,N-1]$ range. For a wider range of options:
- `x:rand(N)/N` for arbitrarily large $N$ will draw a uniform value in $x\in [0,1]$  
- `y:norm_qnt(x)` will convert this to a standard normal variate, using the quantile function of the standard normal.

As a simple example, the code below would be used to calculate the parameters and solutions to a binomial distribution question asking for the probability of observing `k` successes (random draw between 10 and 20) out of `N` trials (random draw between 50 and 100) with a probability of success `p0` (random draw between 0.15 and 0.25). The solution is saved in a variable `sol`.

```
p0: 0.15 + rand(100)/1000
[N,k]:[50+rand(51), 10 + rand(11)]

sol:binom_pdf(N,k,p0)
```

#### Advanced parameter declaration rules

More advanced behaviour is possible:
- Parameters can be booleans (`true` or `false`) or strings (enclosed in `"..."`)
- Parameters can be lists of values, which is useful when one wishes to randomise between a fixed set of alternatives. For example `L:[1.645, 1.96, 2.576]` will declare a list, in this case the 90%, 95% ad 99% two-tailed critical values of the standard normal. Declaring `index:1+rand(3)` will generate a random integer index in the [1,3] inclusive range, and `c:L[index]` will randomly draw one of the three critical values.
- Finally, stackTex allows for conditional parametrisation using `if ... then ... else ...`. As an example, suppose that an exercise asks if one should reject the null hypothesis, where the test statistic `s` is randomly generated and the critical value `c` is obtained as above. The solution and feedback for this random outcome can be set as follows:

```
sol:if abs(s) > c then true else false
txt:if abs(p5) > c then "Reject $H_0$" else "Accept $H_0$"
```

#### Displaying variables in Latex text

Display

### Exercise template fields and options

The various possible settings for a given LaTex exercises are controlled by a  series of options, each flagged by a `\fieldName{option}` decorator.

#### Exercise-level options

The following set of options are set for the entire exercise:

- **category**: *string*, Top-level classification of the exercise, used to categorise the exercise in the question bank compendium. See the `demo\buildFiles\compendium\demo_compendium.pdf` for an illustration.
- **subCategory**: *string*, Sub-level classification of the exercise, used to categorise the exercise in the question bank compendium. See the `demo\buildFiles\compendium\demo_compendium.pdf` for an illustration.
- **exerciseParameters**: *text*, used to declare any parameters used in the exercise. See the [exercise randomisation](#exercise-randomisation) section for instructions.
- **decimalPlaces**: *int*, number of decimal places to use for displaying floating point numbers. Default value is 3 if
- **questionFormat**: *string*, controls the formatting of the list of exercise equations. Options are:
  - **Vlist**: list items are arranged vertically, probably the mode common
  - **HlistMath**: list items are arranged horizontally, with automatic line-breaking . This is designed for basic Maths practice exercises that contain lots of very short questions, where vertical itemisation would take up too much space. See the `demo\raw_latex_exercises\algebra\matrix_operations.tex` example.
  - **ColList**: An alternative to **HlistMath**, where list items are arranged vertically but broken into two side-by-side columns. See the `demo\raw_latex_exercises\algebra\quadratic_roots.tex` example.
- **feedbackFormat**: *string*, controls the formatting of the list of exercise solutions. Options are the same as **questionFormat**.
- **questionBlurb**: *text*, LaTex text for the exercise header.
- **feedbackBlurb**: *text*, LaTex text for the feedback header.

#### Question-level options

An exercise can contain multiple questions, each of which can be configured separately using the following options.

- **questionText**: *text*, LaTex text for the question.
- **questionType**: *string*, sets the question type and controls the STACK algorithm used for assessing quiz answers. Options available are:
  - `Algebraic`: Answer is an algebraic expression, assessed by STACK using the `AlgEquiv` algorithm. Quiz answer is correct if it is algebraically equivalent to the exercise solution. Default setting if `questionType` is left unspecified.
  - `AlgebraicExact`: Answer is an algebraic expression, assessed by STACK using the `EqualComAss` algorithm. Quiz answer is correct if the answer exactly matches the solution up to commutativity and associativity. This is designed for questions where the question and solution are already algebraically equivalent (simplify, factorise, etc.). As an example, if a question asks 'factorise $$x^2+3x+2$$', the solution is $$(x+1)(x+2)$$, yet if assessed using algebraic equivalence an answer of $$x^2+3x+2$$ would be marked as correct. `AlgebraicExact` will only accept $$(x+1)(x+2)$$ or $$(x+2)(x+1)$$.
  - `Numerical`: Answer is an numerical value, assessed by STACK using the `NumAbsolute` algorithm. Quiz answer is correct if the absolute difference with the solution falls below the allowable tolerance set using `tolerance` below.
- **feedbackText**: *text*, LaTex text for the question feedback. If no feedback is provided, the default is to provide a concatenation of the information in the `prompt` and `solution` fields.
- **prompt**: *string*, LaTex answer prompt used in the STACK quiz. Used to
- **tolerance**: *float*, allowable tolerance on numerical answers, used when   `questionType` is set to `Numerical`. If unspecified, a default value of $$0.5\times 10^{-\texttt{decimalPlaces}}$$ is used.
- **solution**: *string*, the solution for the exercise, used as an input to the STACK evaluation algorithms. This can either be a LaTex equation/numerical value or an exercise parameter declared in the `exerciseParameters` section.
- **mark**: *int*, mark awarded for a correct answer.

## Setting up a build file for output generation

If no exercise list is provided in the `exList` field of the JSON file, the toolbox will default to the `compendium` template:
- `build_tex` will build a `.pdf` reference document containing the entire question bank.
- `build_xml` will build a `.xml` file that can be used to import the entire question bank into Moodle.

### Available output templates

The toolbox provides the following 4 templates by default:
- `stack.xml` : This is the main template for exporting exercises to the STACK format for use in Moodle quizzes.
- `compendium.tex` : This template is used to generate a compendium of all exercises in a question bank to be used as a reference d
- `seminar.tex` : A simple template designed to be used as a worksheet or handout.
- `test.tex` : A formatted test/exam template.

More user-defined `.tex` templates can be added, see the [section below](#adding-and-editing-templates) for details.

### Build file fields and options

A build file is a JSON document containing all the instructions required for stackTex to build either a `.tex + .pdf` document or an `.xml` file. There is a minimum requirement for any stackTex build file, detailed below, however each template (including any additional user-added templates) can have their own customisations.

#### Common fields, required for all output templates

The fields below are required for stackTex functionality and should be included in all build files.

- **filename**: *string*, name for the output file.
- **template**: *string*, Latex template to be used for PDF layout. Base options are below, but additional templates can be added:
  - `seminar.tex`
  - `test.tex`
  - `compendium.tex`

The fields below are also required for stackTex functionality, but default behaviours are provided in case the field is not included in the build file.

- **marks"**: *boolean*, flag whether to display marks for the exercise. Set to `false` by default.
- **verbose** *boolean*, flags whether to include verbose feedback. Set to `true` by default.
- **seed**: *int*, seed for the random number generator. Set to 0 by default.
- **exList**: *list*, list of exercises to include in the output file. If exList is not included in the buildFile, `build_tex` and `build_xml` will include all exercises the build.

#### Fields specific to the seminar.tex output template

- **modCode**: *string*, Module code
- **modName**: *string*, Module name.
- **weekNo**: *string*, Week number
- **blurbStr**: *string*, Short description string for event
- **titleStr**: *string*, Title of seminar              

#### Fields specific to the test.tex output template

- **modCode**: *string*, Module code
- **modName**: *string*, Module name
- **lvl**: *int*, Level of qualification studied
- **Day**: *int*, Day of test
- **Mnth**: *string*, Month of test
- **Yr**: *string*, Year of test
- **NoHrs**: *string*, Duration of test
- **QustNo**: *string*, Instruction relating to the number of sections/questions
- **MarkInfo**: *string*, Instructions relating to the marking scheme
- **RmvePaper**: *string*, Instructions relating to the removal of the question paper from examination venue

### Adding and editing output templates

The `.tex` templates are written in standard Latex and can therefore easily be modified to suit the user's specific needs. This would be the case, for example, if the user requires their test or exam document to comply with any requirements set by their institution. Similarly, additional templates can also be added to the toolkit if needed.

Include tokens for location of exercises in document.

`ExStr_1`
