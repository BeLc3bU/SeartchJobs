\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cover}[2026/10/19 Custom Cover Letter Class]
\LoadClass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=2.5cm]{geometry}
\usepackage{parskip}
\usepackage{hyperref}

\newcommand{\header}[4]{
    {\LARGE \textbf{#1}}\\[0.2cm]
    {\large #2}\\[0.1cm]
    \href{https://#3}{#3} \,|\, #4\\[0.4cm]
    \hrule
    \vspace{0.5cm}
}
