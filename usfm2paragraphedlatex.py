
# -*- coding: utf-8 -*-
import re
import textwrap
import argparse
from titlecase import titlecase


LATEX_HEADER = r"""\documentclass[11pt,letterpaper,oneside]{memoir}
\usepackage{charter}

% Set the typeblock size to ensure about 65 characters per line (with Charter 11pt, that's 
% 26 picas).
\settypeblocksize{8.5in}{26pc}{*}
% assuming room for a 3-hole punch (0.625in on the spine)
%\setlrmargins{1.625in}{*}{*}
\setlrmargins{12.5pc}{*}{*}
\setulmargins{1.25in}{*}{*}
\checkandfixthelayout

\pagestyle{companion}

%% Bringhurst chapter style
\makechapterstyle{bringhurst}{%
\renewcommand{\chapterheadstart}{}
\renewcommand{\printchaptername}{}
\renewcommand{\chapternamenum}{}
\renewcommand{\printchapternum}{}
\renewcommand{\afterchapternum}{}
\renewcommand{\printchaptertitle}[1]{%
\raggedright\Large\scshape\MakeLowercase{##1}}
\renewcommand{\afterchaptertitle}{%
\vskip\onelineskip \hrule\vskip\onelineskip}
}

\setsecheadstyle{\raggedright\scshape\MakeLowercase}
\setbeforesecskip{-\onelineskip}
\setaftersecskip{\onelineskip}

\chapterstyle{bringhurst}

\begin{document}
"""

LATEX_FOOTER = r"""\end{document}"""

book_short_header = ''
book_long_header = ''

def read_usfm_verse(line):
    # we've already stripped the verse number out of the line. Now we need to
    # remove some other information tags.
    
    # find wordlist tags and remove them
    pat_wordlist = r"(\\w\s*)(.*?)(\|.*?\\w\*)"
    pat_wordlist_cmp = re.compile(pat_wordlist)

    verse = re.sub(pat_wordlist_cmp, r'\2', line)

    matched_tags = ['\\ADD','\\ND', '\\F']

    pat_all_tags = r"(\\\w+\s*)"
    pat_all_tags_cmp = re.compile(pat_all_tags)

    matches = re.search(pat_all_tags_cmp, verse)
    if matches:
        for match in matches.groups():
            if match.strip().upper() not in matched_tags:
                print(match.strip().upper())

    # delete footnotes
    pat_footnote = r"(\\f\s*)(.*?)(\\f\*)"
    pat_footnote_cmp = re.compile(pat_footnote)
    verse = re.sub(pat_footnote_cmp, '', verse)

    # find 'addition' references
    pat_addition = r"(\\add\s*)(.*?)(\\add\*)"
    pat_addition_cmp = re.compile(pat_addition)
    verse = re.sub(pat_addition_cmp, r'\\emph{\2}', verse)

    # find Names of the Diety
    pat_ND = r"(\\nd\s*)(.*?)(\\nd\*)"
    pat_ND_cmp = re.compile(pat_ND)

    verse = re.sub(pat_ND_cmp, r'\\textsc{\2}', verse)
    
    return verse

def read_usfm_line(line):
    # replace special right quote character
    pat_rsquote = r"’"
    pat_rsquote_cmp = re.compile(pat_rsquote)
    line = re.sub(pat_rsquote_cmp, "'", line)
    
    # pull book ID
    pat_id = r"\\id\s*([\dA-Z]{3})"
    pat_id_cmp = re.compile(pat_id)

    matches = re.match(pat_id_cmp, line)
    if matches:
        book_id = matches.group(1)
        return ''

    # This will be useful for the page headings
    global book_short_header
    pat_book_header = r"\\h\s*(.*)"
    pat_book_header_cmp = re.compile(pat_book_header)
    matches = re.match(pat_book_header_cmp, line)
    if matches:
        book_short_header = matches.group(1).strip()
        return ''

    # these are the main titles. I'll need these later.
    global book_long_header
    pat_mt = r'(\\mt\d)\s*(.*)'
    pat_mt_cmp = re.compile(pat_mt)
    matches = re.match(pat_mt_cmp, line)
    if matches:
        if matches.group(1) == '\\mt1' or matches.group(1) == '\\mt':
            book_long_header = titlecase(matches.group(2)).encode('ascii', 'ignore').strip()
            return ''
        else:
            return ''

    # find the toc entries and delete
    pat_toc = r'\\toc\d\s*'
    pat_toc_cmp = re.compile(pat_toc)
    matches = re.match(pat_toc_cmp, line)
    if matches:
        return ''

    # check for paragraph marker
    pat_para = r"\\p"
    pat_para_cmp = re.compile(pat_para)

    matches = re.match(pat_para_cmp, line)
    if matches:
        return '\n'

    # check for chapter marker; we won't keep it
    pat_chap = r"\\c\s+\d+"
    pat_chap_cmp = re.compile(pat_chap)

    matches = re.match(pat_chap_cmp, line)
    if matches:
        return ''

    # check if verse line, as we'll need to run additional processing
    pat_verse = r"\\v[\s]+[\d]+[\s]+"
    pat_verse_cmp = re.compile(pat_verse)

    match = re.subn(pat_verse_cmp, '', line)
    if match[1] >= 1:
        # found verse, need to continue processing
        line = match[0]
        verse = read_usfm_verse(line)
        return verse
    
    # so we have a line that we're not handling right now... let's print to the
    # console so we can see what's left.
    print(line)

    return ''


def main(inputfile, outputfile):
    output = LATEX_HEADER
    with open(inputfile) as f:
        temp_output = ''
        for line in f:
            temp_line = read_usfm_line(line)

            global book_long_header
            global book_short_header

            if book_long_header <> '' and book_short_header <> '':
                temp_line = r'\chapter[' + book_short_header + ']{' + book_long_header + r'}'
                book_long_header = ''
                book_short_header = ''

            if temp_line == '\n':
                # we must be starting a new paragraph. flush the temp_output
                # to the output and wordwrap
                output += textwrap.fill(temp_output, width=70).strip()
                output += '\n\n'
            
                temp_output = ''
            
            temp_output += temp_line
        
        # flush the final paragraph out
        output += textwrap.fill(temp_output, width=70).strip()
        output += '\n\n'
        output += LATEX_FOOTER

    
    with open(outputfile, 'wb') as f:
        f.write(output)

# parse arguments
parser = argparse.ArgumentParser(
    description='Process USFM-formatted file into paragraphed LaTeX file.')
parser.add_argument('--inputfile', nargs='?',
    help='Input file to process (USFM format)',
    default='93-2JNeng-kjv.usfm')
parser.add_argument('--outputfile', nargs='?',
    help='Output file to create (LaTeX format)',
    default='93-2JNeng-kjv.tex')
args = parser.parse_args()
main(args.inputfile, args.outputfile)