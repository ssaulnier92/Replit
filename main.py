import os
from app import app

if __name__ == '__main__':
    # Render utilise la variable PORT
    port = int(os.environ.get("PORT", 5000))
    # Mode debug désactivé en production
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
