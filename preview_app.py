from flask import Flask, render_template, jsonify, request
import config
import os

app = Flask(__name__)

@app.route('/')
def preview():
    return render_template('preview.html', 
        offset_x=config.LOGO_OFFSET_X,
        offset_y=config.LOGO_OFFSET_Y,
        size=config.LOGO_SIZE,
        opacity=config.LOGO_OPACITY
    )

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'offset_x': config.LOGO_OFFSET_X,
        'offset_y': config.LOGO_OFFSET_Y,
        'size': config.LOGO_SIZE,
        'opacity': config.LOGO_OPACITY
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
