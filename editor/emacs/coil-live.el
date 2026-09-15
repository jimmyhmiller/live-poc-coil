;;; coil-live.el --- Native Coil live programming over nREPL -*- lexical-binding: t; -*-

;; This uses nREPL as transport, but deliberately does not pretend Coil is
;; Clojure. Coil-specific operations and diagnostics stay explicit.

(require 'cl-lib)
(require 'lisp-mode)
(require 'subr-x)
(require 'compile)

;; Adapted from coil-experiments/editor/emacs/coil-live.el (42b1913).
(require 'nrepl-client)

(defgroup coil-live nil "Live Coil development." :group 'languages)

(defcustom coil-live-port-file ".nrepl-port"
  "Project-relative port file written by coil-live-nrepl."
  :type 'string)

(defcustom coil-live-publication-policy "strict"
  "Use strict rejection or publish checked blocked entries with deferred policy."
  :type '(choice (const "strict") (const "deferred")))
(make-variable-buffer-local 'coil-live-publication-policy)

(defvar-local coil-live-connection nil)
(defvar-local coil-live-last-revision nil)
(defvar coil-live-response-hook nil
  "Functions called with RESPONSE and pre-encoding submit time.")

(defun coil-live--namespace ()
  "Read the module declaration without evaluating buffer contents."
  (save-excursion
    (goto-char (point-min))
    (if (re-search-forward "^(module[ \t\n]+\\([[:alnum:]_.-]+\\)[ \t\n]*)" nil t)
        (match-string-no-properties 1)
      (user-error "Buffer needs a module declaration"))))

(defun coil-live--request (fields callback &optional submitted)
  "Send FIELDS with buffer namespace and source location."
  (let* ((connection (coil-live--connection))
         (started (or submitted (float-time))))
    (nrepl-send-request
     (append fields (list "policy" coil-live-publication-policy "ns" (coil-live--namespace)
                          "file-path" (or buffer-file-name "<buffer>")
                          "line" (number-to-string (line-number-at-pos))))
     (lambda (response)
       (run-hook-with-args 'coil-live-response-hook response started)
       (funcall callback response))
     connection)))
(defvar coil-live-connections (make-hash-table :test #'equal)
  "Live nREPL connection buffers keyed by project, host, and port.")
(defvar coil-live-last-state nil)

(define-derived-mode coil-mode lisp-mode "Coil"
  "Major mode for Coil source."
  (setq-local comment-start ";")
  (setq-local comment-start-skip ";+ *"))

(defun coil-live--project-root ()
  (or (locate-dominating-file default-directory "Coil.toml")
      default-directory))

(defun coil-live-connect (&optional host port)
  "Connect this buffer to the project live runtime."
  (interactive)
  (let* ((root (coil-live--project-root))
         (port-file (expand-file-name coil-live-port-file root))
         (token (string-trim
                 (with-temp-buffer
                   (insert-file-contents (expand-file-name ".live-token" root))
                   (buffer-string))))
         (port (or port
                   (and (file-readable-p port-file)
                        (string-to-number
                         (string-trim
                          (with-temp-buffer
                            (insert-file-contents port-file)
                            (buffer-string)))))
                   (read-number "Coil nREPL port: ")))
         (host (or host "127.0.0.1"))
         (key (list (file-truename root) host port))
         (shared (gethash key coil-live-connections)))
    (unless (and (buffer-live-p shared)
                 (process-live-p (get-buffer-process shared)))
      (setq shared
            (process-buffer
             (nrepl-start-client-process
              host port nil
              (lambda (_endpoint)
                (let ((buffer (generate-new-buffer
                               (format " *coil-live %s:%d*" host port))))
                  (with-current-buffer buffer
                    ;; Authentication must precede nREPL's initial clone requests.
                    (setq-local nrepl-session token)
                    (setq-local nrepl-tooling-session token)
                    ;; IDs must remain distinct across connections sharing a world.
                    (setq-local nrepl-request-counter
                                (string-to-number
                                 (substring (secure-hash 'sha256
                                             (format "%s:%s:%s" (emacs-pid)
                                                     (current-time) (random))) 0 32) 16)))
                  buffer)))))
      (puthash key shared coil-live-connections))
    (setq coil-live-connection shared)
    (message "Connected to Coil live runtime on %s:%d" host port)))

(defun coil-live--connection ()
  (or (and coil-live-connection
           (buffer-live-p coil-live-connection)
           (process-live-p (get-buffer-process coil-live-connection))
           coil-live-connection)
      (progn (call-interactively #'coil-live-connect) coil-live-connection)))

(defun coil-live--show-error (response)
  (let ((diagnostic (or (nrepl-dict-get response "err") (nrepl-dict-get response "diagnostic") "Coil edit failed")))
    (with-current-buffer (get-buffer-create "*coil-diagnostics*")
      (let ((inhibit-read-only t))
        (erase-buffer)
        (insert diagnostic)
        (compilation-mode)
        (display-buffer (current-buffer))))))

(defun coil-live--handler (origin)
  (lambda (response)
    (let ((revision (nrepl-dict-get response "revision"))
          (value (nrepl-dict-get response "value")))
      (when (and revision (buffer-live-p origin))
        (with-current-buffer origin (setq coil-live-last-revision revision)))
      (cond
       ((or (nrepl-dict-get response "err")
            (member "blocked" (nrepl-dict-get response "status")))
        (coil-live--show-error response)
        (when revision (message "Coil revision %s has blocked functions" revision)))
       (value (message "%s" value))
       (revision (message "Coil revision %s" revision))))
    (when (member "done" (nrepl-dict-get response "status"))
      (when (buffer-live-p origin)
        (with-current-buffer origin (font-lock-flush))))))

(defun coil-live-eval-region (beg end)
  "Compile and atomically publish the selected Coil forms."
  (interactive "r")
  (let ((submitted (float-time)))
    (coil-live--request
     (list "op" "eval" "code" (buffer-substring-no-properties beg end))
     (coil-live--handler (current-buffer)) submitted)))

(defun coil-live-eval-defun ()
  "Compile and publish the top-level form at point."
  (interactive)
  (save-excursion
    (end-of-defun)
    (let ((end (point)))
      (beginning-of-defun)
      (coil-live-eval-region (point) end))))

(defun coil-live-load-buffer ()
  "Submit the buffer as one live edit transaction."
  (interactive)
  (coil-live--request
   (list "op" "load-file"
         "file" (buffer-substring-no-properties (point-min) (point-max))
         "file-path" (or buffer-file-name "<buffer>"))
   (coil-live--handler (current-buffer))))

(defun coil-live-state ()
  "Inspect the shared application's accepted revision."
  (interactive)
  (nrepl-send-request
   '("op" "status")
   (lambda (response)
     (setq coil-live-last-state response)
     (message "Coil accepted revision %s" (nrepl-dict-get response "revision")))
   (coil-live--connection)))

(define-key coil-mode-map (kbd "C-c C-c") #'coil-live-eval-defun)
(define-key coil-mode-map (kbd "C-c C-r") #'coil-live-eval-region)
(define-key coil-mode-map (kbd "C-c C-k") #'coil-live-load-buffer)
(define-key coil-mode-map (kbd "C-c C-z") #'coil-live-state)

(add-to-list 'auto-mode-alist '("\\.coil\\'" . coil-mode))

(provide 'coil-live)
;;; coil-live.el ends here
