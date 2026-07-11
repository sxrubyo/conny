cd /home/ubuntu/bublee
for f in fix_init.py scratch_regex.py test_conversation.py test_llm_prod.py test_melissa.py runtime.py test_browser.js; do
    if [ -f "$f" ]; then
        mv "$f" legacy/ && echo "MOVED $f"
    else
        echo "SKIP $f"
    fi
done
echo "ROOT .PY COUNT:"
ls *.py 2>/dev/null | wc -l
echo "LEGACY COUNT:"
ls legacy/ | wc -l
