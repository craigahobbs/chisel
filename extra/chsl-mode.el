;;; chsl-mode.el --- major mode for editing CHisel Specification Language.

;; Version: 0.1

;;; Commentary:

;; To install, add the following to your .emacs file:

;; (package-initialize)
;;
;; (unless (package-installed-p 'chsl-mode)
;;   (let ((chsl-mode-file (make-temp-file "chsl-mode")))
;;     (url-copy-file "https://raw.githubusercontent.com/craigahobbs/chisel/master/extra/chsl-mode.el" chsl-mode-file t)
;;     (package-install-file chsl-mode-file)
;;     (delete-file chsl-mode-file)))
;; (add-to-list 'auto-mode-alist '("\\.chsl?\\'" . chsl-mode))

;;; Code:
(require 'generic-x)

;;;###autoload
(define-generic-mode 'chsl-mode
      '("#")
      '(
        "action"
        "enum"
        "errors"
        "group"
        "input"
        "nullable"
        "optional"
        "output"
        "struct"
        "union"
        "url"
        )
      (list
       (cons
        (regexp-opt
         '(
           "bool"
           "date"
           "datetime"
           "float"
           "int"
           "object"
           "string"
           "uuid"
           ) 'words) 'font-lock-type-face)
        )
      '(".chsl\\'")
      nil
      "Major mode for editing CHisel Specification Language")

(provide 'chsl-mode)
;;; chsl-mode.el ends here
