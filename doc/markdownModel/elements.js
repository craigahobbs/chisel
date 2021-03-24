// Licensed under the MIT License
// https://github.com/craigahobbs/chisel/blob/master/LICENSE

import {getBaseURL, isAbsoluteURL} from '../elementModel/util.js';
import {markdownModel} from './markdownModel.js';
import {validateType} from '../schemaMarkdown/schema.js';


/**
 * Generate an element model from a markdown model
 *
 * @param {Object} markdown - The markdown model
 * @param {?string} url - The markdown file's URL
 * @param {?Object} codeBlockLanguages - Optional map of language to code block render function with signature (lines) => elements.
 * @returns {Object[]}
 */
export function markdownElements(markdown, url = null, codeBlockLanguages = null) {
    // Parse the markdown
    const validatedMarkdown = validateType(markdownModel.types, 'Markdown', markdown);

    // Generate an element model from the markdown model parts
    return markdownPartElements(validatedMarkdown.parts, url, codeBlockLanguages);
}


/**
 * Helper function to generate an element model from a markdown part model array
 *
 * @param {Object[]} parts - The markdown parts model array
 * @param {?string} url - The markdown file's URL
 * @param {?Object} codeBlockLanguages - Optional map of language to code block render function with signature (lines) => elements.
 * @returns {Object[]} The parts array element model
 */
function markdownPartElements(parts, url, codeBlockLanguages) {
    const partElements = [];
    for (const markdownPart of parts) {
        // Paragraph?
        /* istanbul ignore else */
        if ('paragraph' in markdownPart) {
            const {paragraph} = markdownPart;
            partElements.push({
                'html': 'style' in paragraph ? paragraph.style : 'p',
                'elem': paragraphSpanElements(paragraph.spans, url)
            });

        // Horizontal rule?
        } else if ('hr' in markdownPart) {
            partElements.push({'html': 'hr'});

        // List?
        } else if ('list' in markdownPart) {
            const {list} = markdownPart;
            partElements.push({
                'html': 'start' in list ? 'ol' : 'ul',
                'attr': 'start' in list && list.start > 1 ? {'start': `${list.start}`} : null,
                'elem': list.items.map((item) => ({
                    'html': 'li',
                    'elem': markdownPartElements(item.parts, url, codeBlockLanguages)
                }))
            });

        // Code block?
        } else if ('codeBlock' in markdownPart) {
            const {codeBlock} = markdownPart;

            // Render the code block elements
            if (codeBlockLanguages !== null && 'language' in codeBlock && codeBlock.language in codeBlockLanguages) {
                partElements.push(codeBlockLanguages[codeBlock.language](codeBlock));
            } else {
                partElements.push(
                    {'html': 'pre', 'elem': {'html': 'code', 'elem': codeBlock.lines.map((line) => ({'text': `${line}\n`}))}}
                );
            }
        }
    }

    return partElements;
}


/**
 * Helper function to generate an element model from a markdown span model array
 *
 * @param {Object[]} spans - The markdown span model array
 * @param {?string} url - The markdown file's URL
 * @returns {Object[]} The span array element model
 */
function paragraphSpanElements(spans, url) {
    const spanElements = [];
    for (const span of spans) {
        // Text span?
        /* istanbul ignore else */
        if ('text' in span) {
            spanElements.push({'text': span.text});

        // Line break?
        } else if ('br' in span) {
            spanElements.push({'html': 'br'});

        // Style span?
        } else if ('style' in span) {
            const {style} = span;
            spanElements.push({
                'html': style.style === 'italic' ? 'em' : 'strong',
                'elem': paragraphSpanElements(style.spans, url)
            });

        // Link span?
        } else if ('link' in span) {
            const {link} = span;
            const href = url !== null && !isAbsoluteURL(link.href) ? `${getBaseURL(url)}${link.href}` : link.href;
            const linkElements = {
                'html': 'a',
                'attr': {'href': href},
                'elem': paragraphSpanElements(link.spans, url)
            };
            if ('title' in link) {
                linkElements.attr.title = link.title;
            }
            spanElements.push(linkElements);

        // Image span?
        } else if ('image' in span) {
            const {image} = span;
            const src = url !== null && !isAbsoluteURL(image.src) ? `${getBaseURL(url)}${image.src}` : image.src;
            const imageElement = {
                'html': 'img',
                'attr': {'src': src, 'alt': image.alt}
            };
            if ('title' in image) {
                imageElement.attr.title = image.title;
            }
            spanElements.push(imageElement);
        }
    }
    return spanElements;
}
