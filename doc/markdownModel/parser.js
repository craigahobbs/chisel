// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE


// Markdown regex
const rIndent = /^(?<indent>\s*)(?<notIndent>.*)$/;
const rHeading = /^\s*(?<heading>#{1,6})\s+(?<text>.*?)\s*$/;
const rHeadingAlt = /^\s*(?<heading>=+|-+)\s*$/;
const rHorizontal = /^(?:(?:\s*\*){3,}|(?:\s*-){3,}|(?:\s*_){3,})\s*$/;
const rFenced = /^(?<fence>\s*(?:`{3,}|~{3,}))(?:\s*(?<language>.+?))?\s*$/;
const rList = /^(?<indent>\s*(?<mark>-|\*|\+|[0-9]\.|[1-9][0-9]+\.)\s+)(?<line>.*?)\s*$/;
const rSpans = new RegExp(
    '(?<br>\\s{2}$)|' +
        '(?<link>!?\\[)(?<linkText>[\\s\\S]*?)\\]\\((?<linkHref>[^\\s]+?)(?:\\s*"(?<linkTitle>[\\s\\S]*?)"\\s*)?\\)|' +
        '(?<linkAlt><)(?<linkAltHref>[[a-z]+:[^\\s]*?)>|' +
        '(?<boldItalic>\\*{3})(?!\\s)(?<boldItalicText>[\\s\\S]*?[^\\s]\\**)\\*{3}|' +
        '(?<bold>\\*{2})(?!\\s)(?<boldText>[\\s\\S]*?[^\\s]\\**)\\*{2}|' +
        '(?<italic>\\*)(?!\\s)(?<italicText>[\\s\\S]*?[^\\s]\\**)\\*',
    'mg'
);
const rEscape = /\\(\\|\*|_|\{|\}|\[|\]|\(|\)|#|\+|-|\.|!)/g;


/**
 * Parse markdown text or text lines into a markdown model
 *
 * @param {string|string[]} markdown - Markdown text or text lines
 * @returns {Object} The markdown model
 */
export function markdownParse(markdown) {
    const markdownParts = [];
    const parts = [[0, null, 0]];
    let paragraph = null;
    let paragraphFenced = null;
    let lines = [];

    // Helper function to add a markdown part
    const addPart = (part) => {
        const [, topList] = parts[parts.length - 1];
        if (topList !== null) {
            const {items} = topList.list;
            items[items.length - 1].parts.push(part);
        } else {
            markdownParts.push(part);
        }
    };

    // Helper function to close the current part
    const closeParagraph = (paragraphStyle = null) => {
        // Code block?
        if (paragraph !== null) {
            // Strip trailing blank lines
            let ixLine;
            for (ixLine = lines.length - 1; ixLine >= 0; ixLine--) {
                if (lines[ixLine] !== '') {
                    break;
                }
            }
            paragraph.codeBlock.lines = lines.splice(0, ixLine + 1);
            paragraph = null;
            paragraphFenced = null;
        } else if (lines.length) {
            // Paragraph
            const paragraphPart = {'paragraph': {'spans': paragraphSpans(lines.join('\n'))}};
            if (paragraphStyle !== null) {
                paragraphPart.paragraph.style = paragraphStyle;
            }
            addPart(paragraphPart);
        }
        lines = [];
    };

    // Helper function to get the correct [indent, list, listIndent] tuple for the given indent
    const updateParts = (indent, isList = false) => {
        // Find the part with the lesser or equal indent
        for (let ixPart = parts.length - 1; ixPart > 0; ixPart--) {
            const [curIndent,, curListIndent] = parts[ixPart];
            if (indent >= (isList ? curListIndent : curIndent)) {
                break;
            }
            parts.pop();
        }
        return parts[parts.length - 1];
    };

    // Helper function to add a paragraph line
    const addLine = (line, lineIndent, codeBlockIndent) => {
        if (lines.length) {
            // Code block line? If so, trip the indent
            if (paragraph !== null) {
                lines.push(line.slice(codeBlockIndent));
            } else {
                lines.push(line);
            }
        } else {
            const [curIndent] = updateParts(lineIndent);
            lines.push(line.slice(curIndent));
        }
    };

    // Process markdown text line by line
    for (const markdownString of (typeof markdown === 'string' ? [markdown] : markdown)) {
        for (const line of markdownString.split('\n')) {
            const matchLine = line.match(rIndent);
            const lineIndent = matchLine.groups.indent.length;
            const emptyLine = matchLine.groups.notIndent === '';
            const matchHeading = emptyLine ? null : line.match(rHeading);
            const matchHeadingAlt = emptyLine ? null : line.match(rHeadingAlt);
            const matchFenced = emptyLine ? null : line.match(rFenced);
            const matchList = emptyLine ? null : line.match(rList);
            const [topIndent] = parts[parts.length - 1];
            const codeBlockIndent = topIndent + 4;

            // Empty line?
            if (emptyLine) {
                // Close any open paragraph
                if (paragraph !== null) {
                    addLine(line, lineIndent, topIndent);
                } else {
                    closeParagraph();
                }

            // Code block start?
            } else if (!lines.length && lineIndent >= codeBlockIndent) {
                // Add the code block part
                paragraph = {'codeBlock': {}};
                addPart(paragraph);
                lines.push(line.slice(codeBlockIndent));

            // Fenced code start?
            } else if (paragraphFenced === null && matchFenced !== null && lineIndent < codeBlockIndent) {
                // Close any open paragraph
                closeParagraph();

                // Add the code block part
                paragraph = {'codeBlock': {}};
                if (typeof matchFenced.groups.language !== 'undefined') {
                    paragraph.codeBlock.language = matchFenced.groups.language;
                }
                paragraphFenced = matchFenced.groups.fence;
                addPart(paragraph);

            // Fenced code end?
            } else if (paragraphFenced !== null && matchFenced !== null && paragraphFenced.startsWith(matchFenced.groups.fence) &&
                       typeof matchFenced.groups.language === 'undefined') {
                // Close the code block
                closeParagraph();

            // Fenced code line?
            } else if (paragraphFenced !== null && matchFenced === null) {
                // Add the code line
                addLine(line, lineIndent, topIndent);

            // Heading?
            } else if (matchHeading !== null && lineIndent < codeBlockIndent) {
                // Close any open paragraph
                closeParagraph();

                // Add the heading paragraph markdown part
                updateParts(lineIndent);
                lines = [matchHeading.groups.text];
                closeParagraph(`h${matchHeading.groups.heading.length}`);

            // Heading (alternate syntax)?
            } else if (matchHeadingAlt !== null && lineIndent < codeBlockIndent && parts.length === 1 &&
                       lines.length && paragraph === null) {
                // Add the heading paragraph markdown part
                closeParagraph(matchHeadingAlt.groups.heading.startsWith('=') ? 'h1' : 'h2');

            // Horizontal rule?
            } else if (rHorizontal.test(line) && lineIndent < codeBlockIndent) {
                // Close any open paragraph
                closeParagraph();

                // Add the heading paragraph markdown part
                updateParts(lineIndent);
                addPart({'hr': null});

            // List?
            } else if (matchList !== null && lineIndent < codeBlockIndent) {
                // Close any open paragraph
                closeParagraph();

                // New list?
                const [curIndent, curList] = updateParts(lineIndent, true);
                if (curList === null || lineIndent >= curIndent) {
                    // Add the new list part
                    const list = {'list': {'items': [{'parts': []}]}};
                    const start = parseInt(matchList.groups.mark, 10);
                    if (!isNaN(start)) {
                        list.list.start = start;
                    }
                    addPart(list);
                    parts.push([matchList.groups.indent.length, list, lineIndent]);
                } else {
                    // Push the new list item
                    const listItem = {'parts': []};
                    curList.list.items.push(listItem);
                }

                // Add the text line
                lines.push(matchList.groups.line);

            // Text line
            } else {
                // End code block first?
                if (paragraph !== null && lineIndent < codeBlockIndent) {
                    closeParagraph();
                }

                // Add the paragraph line
                addLine(line, lineIndent, codeBlockIndent);
            }
        }
    }

    // Close any open paragraph
    closeParagraph();

    return {'parts': markdownParts};
}


/**
 * Helper function to remove escapes from a string
 *
 * @param {string} text - The text to remove escapes from
 * @returns {string}
 */
function removeEscapes(text) {
    return text.replace(rEscape, '$1');
}


/**
 * Helper function to translate markdown paragraph text to a markdown paragraph span model array
 *
 * @param {string} text - The markdown text
 * @returns {Object[]} The markdown paragraph span array model
 */
function paragraphSpans(text) {
    const spans = [];

    // Iterate the span matches
    let ixSearch = 0;
    for (const match of text.matchAll(rSpans)) {
        // Add any preceding text
        if (ixSearch < match.index) {
            spans.push({'text': removeEscapes(text.slice(ixSearch, match.index))});
        }


        // Line break?
        /* istanbul ignore else */
        if (typeof match.groups.br !== 'undefined') {
            spans.push({'br': null});

        // Link span?
        } else if (match.groups.link === '[') {
            const span = {'link': {'href': removeEscapes(match.groups.linkHref), 'spans': paragraphSpans(match.groups.linkText)}};
            if (typeof match.groups.linkTitle !== 'undefined') {
                span.link.title = removeEscapes(match.groups.linkTitle);
            }
            spans.push(span);

        // Link span (alternate syntax)?
        } else if (match.groups.linkAlt === '<') {
            spans.push({'link': {'href': removeEscapes(match.groups.linkAltHref), 'spans': paragraphSpans(match.groups.linkAltHref)}});

        // Image span?
        } else if (match.groups.link === '![') {
            const span = {'image': {'src': removeEscapes(match.groups.linkHref), 'alt': removeEscapes(match.groups.linkText)}};
            if (typeof match.groups.linkTitle !== 'undefined') {
                span.image.title = removeEscapes(match.groups.linkTitle);
            }
            spans.push(span);

        // Bold-italic style-span
        } else if (match.groups.boldItalic === '***') {
            spans.push({'style': {'style': 'bold', 'spans': [
                {'style': {'style': 'italic', 'spans': paragraphSpans(match.groups.boldItalicText)}}
            ]}});

        // Bold style-span
        } else if (match.groups.bold === '**') {
            spans.push({'style': {'style': 'bold', 'spans': paragraphSpans(match.groups.boldText)}});

        // Italic style-span
        } else if (match.groups.italic === '*') {
            spans.push({'style': {'style': 'italic', 'spans': paragraphSpans(match.groups.italicText)}});
        }

        ixSearch = match.index + match[0].length;
    }

    // Add any remaining text
    if (ixSearch < text.length) {
        spans.push({'text': removeEscapes(text.slice(ixSearch))});
    }

    return spans;
}
