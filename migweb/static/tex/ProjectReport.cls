\NeedsTeXFormat{LaTeX2e}[1994/06/01]
\ProvidesClass{ProjectReport}[2009/05/15 v0.0.1 Document class for typesetting TBP Project Reports]
\usepackage{enumerate}
\usepackage{float}

\usepackage{ifthen}
 
\newcommand{\newoddside}{
        \ifthenelse{\isodd{\thepage}}{
        \newpage
        \phantom{placeholder} % doesn't appear on page
        \thispagestyle{empty} % if want no header/footer
        \newpage
        }{\newpage}
}
\newcommand{\newevenside}{
        \ifthenelse{\isodd{\thepage}}{\newpage}{
        \newpage
        \phantom{placeholder} % doesn't appear on page
        \thispagestyle{empty} % if want no header/footer
        \newpage
        }
}
\newcommand{\blankpage}{
 	\newpage
        \phantom{placeholder} % doesn't appear on page
        \thispagestyle{empty} % if want no header/footer
        \newpage
}

\LoadClass[12pt,letterpaper]{report}
\usepackage[colorlinks=true]{hyperref}
%\usepackage{wrapfig}
\hypersetup{
    colorlinks,
    citecolor=black,
    filecolor=black,
    linkcolor=black,
    urlcolor=black
}
\newcommand{\newproject}[1]{\centering \section*{#1}}
\RequirePackage{xspace}
\newcommand{\schoolyear}[1]{\def\@schoolyear{#1\xspace}}
\newcommand{\historian}[1]{\def\@historian{#1\xspace}}
\newcommand{\preparertitle}[1]{\def\@preparertitle{#1\xspace}}
\newcommand{\sigFile}[1]{\def\@sigFile{#1}}
\newcommand{\paraspace}{\\[0.3cm]}
\newcommand{\signaturespace}{\\[1in]}
\newcommand{\forceLine}{\\}
\newcommand{\semester}[1]{\chapter*{#1}\addcontentsline{toc}{chapter}{#1}\newevenside}
\renewcommand{\abstractname}{Overview}
\setcounter{secnumdepth}{0}
\makeatletter

\renewcommand{\maketitle}{
\newpage
 \null

\thispagestyle{empty}
 \begin{center}
  \quad\\[2 in]
  \bf \LARGE The Michigan Gamma Chapter of Tau~Beta~Pi\\ Presents: \\[3 in]
 \bf \huge Project Reports for the \\ \@schoolyear \\Annual Chapter Survey
 \end{center}
\newoddside
\section*{}
\thispagestyle{empty}
I proudly present to you the Project Reports for the \@schoolyear Michigan Gamma Annual Chapter Survey. The Chapter Survey itself has been submitted online and this document provides supplemental information about each individual project. This report, along with the submitted Chapter survey, marks the end of another successful year for the Michigan Gamma chapter and represents countless hours of dedicated hard work by many people. \paraspace
Many new faces joined our officer corps this year, and with these new officers came fresh ideas and inspiration for our chapter. It is my hope that the coming year will be a productive one for Michigan Gamma, and that we will see the continuation of efforts begun in the past year, as well as the beginning of some new and exciting projects.\paraspace
The contributions of all the officers, project chairs, and participating members were greatly appreciated. I feel that our efforts have produced a terrific survey and represent our chapter's activities to the best of our ability.\paraspace~\paraspace
Sincerely,\\
\includegraphics[width=2in]{\@sigFile}\\
\@historian
\\ MI-$\Gamma$ \@preparertitle~\@schoolyear 
\newoddside
\begin{abstract}
This section lists all of the projects performed by the Michigan Gamma Chapter of Tau Beta Pi for the school year extending from September 2011 to May 2012. The projects presented here were categorized into five separate groups:
\begin{enumerate}[1.]
\item Professional: Projects which were performed to enhance the engineering skills and job opportunities for students as well as offer opportunities for students to interact with company representatives.
\item Community: Projects which were performed primarily as a service to the community and undertaken to enhance a spirit of liberal culture within the chapter.
\item University: Projects which were performed primarily as a service to the University and its students.
\item Chapter: Projects which were performed to aid to smooth operation of the chapter, stimulate the interaction between other chapters in the nation, or stimulate social interaction of our members within the college, with each other, and with other societies.
\item Honors: Projects which were performed to honor outstanding achievement within our chapter and the University.
\end{enumerate}
Each project occupies at least one sheet, the Chapter Project Summary. The summary was derived from the standard Project Report provided by the national organization. There is one summary sheet for each project; however, some projects were repeated in different weeks or semesters. For simplicity, some of the sections above were split into the fall and winter semester for the school year. Unfortunately, for some projects a complete list of participants was not available due to the large number of members.
\end{abstract}
\newoddside
\tableofcontents
\newevenside

} \makeatother

\RequirePackage[margin=1in]{geometry}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{amsthm}
\RequirePackage[usenames,dvipsnames]{color}
\RequirePackage{graphicx}
\RequirePackage[export]{adjustbox}
%	\graphicspath{ {./Images/}}
\usepackage{url}
\RequirePackage{listings}

\RequirePackage{tikz}
\usetikzlibrary{arrows,snakes,patterns}


\RequirePackage{hyperref}

\renewcommand{\theenumi}{\alph{enumi}}

\newfloat{PageHeader}{H}{pgh}
\usepackage{longtable}