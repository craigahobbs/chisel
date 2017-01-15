;;; chsl-mode.el --- major mode for editing CHisel Specification Language.

;; Version: 0.1

;;; Commentary:

;; To install, add the following to your .emacs file:

;; (package-initialize)
;; (unless (package-installed-p 'chsl-mode)
;;   (let ((chsl-mode-file (make-temp-file "chsl-mode")))
;;     (message "Installing chsl-mode")
;;     (url-copy-file "https://raw.githubusercontent.com/craigahobbs/chisel/master/extra/chsl-mode.el" chsl-mode-file t)
;;     (package-install-file chsl-mode-file)
;;     (delete-file chsl-mode-file))
;; (add-to-list 'auto-mode-alist '("\\.chsl?\\'" . chsl-mode))

;;; Code:

;; define several category of keywords
(setq chsl-keywords '("action" "enum" "errors" "group" "input" "nullable" "optional" "output" "struct" "union"))
(setq chsl-types '("bool" "date" "datetime" "float" "int" "object" "string" "uuid"))

;; generate regex string for each category of keywords
(setq chsl-keywords-regexp (regexp-opt chsl-keywords 'words))
(setq chsl-type-regexp (regexp-opt chsl-types 'words))

;; create the list for font-lock.
;; each category of keyword is given a particular face
(setq chsl-font-lock-keywords
      `(
        (,chsl-type-regexp . font-lock-type-face)
        (,chsl-keywords-regexp . font-lock-keyword-face)
        ))

;;;###autoload
(define-derived-mode chsl-mode python-mode "chsl mode"
  "Major mode for editing CHisel Specification Language"
  (setq font-lock-defaults '((chsl-font-lock-keywords))))

(provide 'chsl-mode)
;;; chsl-mode.el ends here
