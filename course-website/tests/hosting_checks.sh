#!/usr/bin/env bash
# Hosting checks against a running server. Usage: tests/hosting_checks.sh http://127.0.0.1:8080
B=${1:-http://127.0.0.1:8080}
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1  (expected '$3', got '$2')"; fail=$((fail+1)); fi; }
has()   { if echo "$2" | grep -qi "$3"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1  (missing '$3')"; fail=$((fail+1)); fi; }
code()  { curl -s -o /dev/null -w "%{http_code}" "$@"; }
hdr()   { curl -s -D - -o /dev/null "$@"; }

check "home page /                    returns 200" "$(code $B/)" 200
check "index.html                     returns 200" "$(code $B/index.html)" 200
check "robots.txt                     returns 200" "$(code $B/robots.txt)" 200
check "styles.css (404 page styling)  returns 200" "$(code $B/styles.css)" 200
check "unknown page                   returns 404" "$(code $B/no-such-page)" 404
has   "unknown page shows custom 404 page" "$(curl -s $B/no-such-page)" "This page doesn't exist"
check ".htaccess is not downloadable  (403)" "$(code $B/.htaccess)" 403
check "directory listing disabled     (no index -> 403/404)" "$(mkdir -p /var/www/bootcamp/emptydir; c=$(code $B/emptydir/); rmdir /var/www/bootcamp/emptydir; [ $c = 403 -o $c = 404 ] && echo ok || echo $c)" ok
H=$(hdr $B/)
has   "HTML served as text/html; charset utf-8" "$H" "Content-Type: text/html"
has   "X-Content-Type-Options: nosniff" "$H" "X-Content-Type-Options: nosniff"
has   "Referrer-Policy set" "$H" "Referrer-Policy: strict-origin-when-cross-origin"
has   "HTML not cached long (max-age=0)" "$H" "max-age=0"
G=$(hdr -H "Accept-Encoding: gzip" $B/)
has   "gzip compression on HTML" "$G" "Content-Encoding: gzip"
C=$(hdr -H "Accept-Encoding: gzip" $B/styles.css)
has   "CSS cached for 7 days" "$C" "max-age=604800"
has   "CSS compressed" "$C" "Content-Encoding: gzip"
R=$(hdr $B/robots.txt)
has   "robots.txt served as text/plain" "$R" "Content-Type: text/plain"
full=$(curl -s $B/ | wc -c); gz=$(curl -s -H "Accept-Encoding: gzip" $B/ | wc -c)
echo "INFO  page size: ${full} bytes raw, ${gz} bytes over the wire (gzip)"
t=$(curl -s -o /dev/null -w "%{time_total}" $B/); echo "INFO  server response time: ${t}s (local)"
echo "------"; echo "hosting checks: $pass passed, $fail failed"; [ $fail = 0 ]
