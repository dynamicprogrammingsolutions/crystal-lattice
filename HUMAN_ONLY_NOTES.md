Simple debugging:

```bash
# In one terminal
crystal --console --log-level DEBUG --log-file ./local.log

# In another terminal
tail -f -l 1 ./local.log

# Notes:
# Press Ctrl+K before doing the problematic action
# Search the terminal if needed
# Some terminals have a buffer limit, you may need to increase it if the logs are too long
```

