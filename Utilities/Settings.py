
# Size of the window in PyQT
min_window_width = 1000
min_window_height = 650
window_width = 1000
window_height  = 650
window_strecth_factor = 1
menu_window_width = 200

# Define window names
main_window_name = "MainVisualization"

# Define the color scheme with rgb values
background_color = "background-color: black;"
button_color = "background-color: #676767;"


# Menu font for the menu bar
menu_font = "QLabel { color: DarkBlue; font-weight: bold; font-style: italic; \
                    font-family: Comic Sans MS; }"

# Header font for the menu bar
header_font = "QLabel { color: green; font-weight: bold; \
    font-size: 16px; font-style: italic; font-family: Comic Sans MS; }"


# CSS based styles
button_style = "QPushButton { background-color: orange; border-style: outset; \
    border-width: 4px; border-radius: 12px; border-color: black; padding: 4px; }"



# style sheet for visualization widget
vis_style_menu = "QFrame { background-color: rgba(230, 230, 230, 255); }"
vis_style_multiple = "QFrame { background-color: rgba(230, 230, 230, 255); }"
vis_style_single = "QFrame { background-color: rgba(0, 0, 0, 255); }"




# Data settings
im_train_path   = "Data/CT/Train/Images"
mask_train_path = "Data/CT/Train/Masks"
im_test_path    = "Data/CT/Test/Images"


# View coordinate system
coordinate_system = {
    'color' : (0./255 ,255./255, 255./255),
    'plane_color' : (255./255, 255./255, 255./255)
}


# visualization text color
vis_text_info = {
    'size' : 24,
    'color' : (255./255, 20./255, 20./255),
    'position' : (20, 20)
}

# Active organs
organs = ['left ventricle', 'right ventricle', 'left atrium',
        'right atrium', 'ascending aorta', 'pulmonary artery']

# Values for each organ
labels = {
    'left ventricle'   : {'value': 500, 'rgb' : (65./255, 105./255, 225./255), 'color' : 'blue'},
    'right ventricle'  : {'value': 600, 'rgb' : (0., 1., 0.), 'color' : 'green'},
    'left atrium'      : {'value': 420, 'rgb' : (255./255, 182./255, 193./255), 'color' : 'pink'},
    'right atrium'     : {'value': 550, 'rgb' : (1., 140./255, 0.), 'color' : 'orange'},
    'myocardium LV'    : {'value': 205, 'rgb' : (1., 1., 1.), 'color' : 'white'},
    'ascending aorta'  : {'value': 820, 'rgb' : (1., 0., 0.), 'color' : 'red'},
    'pulmonary artery' : {'value': 850, 'rgb' : (139./255, 0./255, 139./255), 'color' : 'purple'},
}

view_icons = {
    'path' : 'Utilities/FugueIcons/icons/',
    'menu_buttons': {
        'Crosshair Mode' : {'png' : 'arrow-out.png'},
        'Zoom Mode' : {'png' : 'magnifier-zoom-fit.png'},
        'Reset Mode' : {'png' : 'border-outside.png'},
        'Point Mode' : {'png' : 'palette-paint-brush.png'},
        'Histogram Mode' : {'png' : 'application-plus-black.png'}
    },
    'point_buttons': {
        'delete' : {
            'selected' : 'block--minus.png',
            'all'      : 'cross-script.png'
        },
        'improve' : {
            'selected' : 'block--plus.png',
            'all'      : 'tick.png'
        }
    }
}


'brain-empty.png'
'brain.png'

colormaps = [
    'viridis',
    'binary',
    'gist_yarg',
    'gist_gray',
    'gray',
    'bone',
    'pink',
    'spring',
    'summer',
    'autumn',
    'winter',
    'cool',
    'Wistia',
    'hot',
    'afmhot',
    'gist_heat',
    'copper',
    'jet'
]
