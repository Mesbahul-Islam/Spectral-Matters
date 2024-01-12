import os 
import numpy as np
import guilib as glib

# state dictionary to maintain program state
state = {
        "textbox": None,
        "points" : [],
        "data" : None,
        "plotted" : False,
        "data_loaded": False,
        "dependency" : False,
        "intensity" : False,
        "canvas" : None,
        "button_pressed" : False
    }
def reset_state_dic(key):
    """
    Resets the state dictionary according to the argument
    """
    if key == "all":
        state["data"] = None
        state["points"] = []
        state["canvas"] = None
    elif key == "points":
        state["points"] = []
def read_data(folder):
    """
    Reads all data files from the given folder. Skips files that don't have the
    .txt extension and files that have errors in them. The names of faulty .txt
    files are reported to the user.

    :param folder: folder to read
    """
    faulty_data = []
    bind_list = None 
    inten_list = None
    files_read = 0
    if not os.path.exists(folder) or not os.path.isdir(folder):
        raise ValueError("Folder path does not exist")
    for filename in os.listdir(folder):
        if filename.endswith("txt"):
            file_path = os.path.join(folder, filename)
            try:
                file_data = np.loadtxt(file_path).T #T is transpose, otherwise the array is just 2 columns. 
                if bind_list is None: #code borrowed from numpy documentation https://numpy.org/doc/1.26/reference/generated/numpy.loadtxt.html
                    bind_list = file_data[0]
                    inten_list = np.zeros_like(bind_list) #Creating a numpy array the size of bind_list
                inten_list += file_data[1]
                files_read += 1
            except Exception as e: # Exception statement borrowed from 
                faulty_data.append(filename) # https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python
        else:
            faulty_data.append(filename)
    if not files_read:
        message = "No readable files. Please select another folder"
        glib.write_to_textbox(state["textbox"], message)
    else:
        state["data_loaded"] = True
    return bind_list, inten_list, faulty_data
def open_folder():
    """
    A button handler that opens a dialog the user can use to choose a data folder.
    Loads data from the selected folder and reports the number of rows read and the
    names of any faulty files into a textbox.
    """
    folder = glib.open_folder_dialog("Insert folder")
    if folder:
        if os.path.isdir(folder):
            bind_data, intensity_data, faulty = read_data(folder)
            try:
                state["data"] = (bind_data, intensity_data)
                glib.write_to_textbox(state["textbox"], f"Read {len(bind_data)} lines of data") 
            except (ValueError, IOError):
                message = "Could not read folder"
                glib.write_to_textbox(state["textbox"], message)
        else:
            message = "Could not read folder"
            glib.write_to_textbox(state["textbox"], message)
        if faulty:
            for item in faulty:
                message = f"Faulty: {item}"
                glib.write_to_textbox(state["textbox"], message)
    else:
        message = "Folder does not exist. Please try again"
        glib.write_to_textbox(state["textbox"], message)
def choose_point(mouse_event):
    """
    Receives a mouse event from a mouse click and reads the x and y data 
    values from it. The values are printed into a textbox, and saved to a list
    in the program's state dictionary. Also checks if the point is inside or outside the graph
    Numpy functions from
    https://numpy.org/doc/stable/reference/generated/numpy.round.html
    https://numpy.org/doc/stable/reference/generated/numpy.any.html
    """
    if not state["dependency"] and not state["intensity"]:
        glib.write_to_textbox(state["textbox"], "Please click 'Remove Linear Dependency' or 'Calculate Intensities' first.")
    else:
        x = mouse_event.xdata
        y = mouse_event.ydata
        x_tocheck = round(x)
        y_tocheck = round(y)
        x_data, y_data = state["data"]
        if np.any(np.round(x_data) == x_tocheck) and np.any(np.round(y_data) == y_tocheck):
            values = (x, y)
            message = f"Point selected = ({x:.2f} , {y:.2f})"
            glib.write_to_textbox(state["textbox"], message)
            state["points"].append(values)
            if len(state["points"]) == 2:
                state["button_pressed"] = True
                if state["button_pressed"]:
                    message = f"Click {'Remove Linear Dependency' if state['dependency'] else 'Calculate intensity'} again"
                    glib.write_to_textbox(state["textbox"], message)
                    state["button_pressed"] = False
        else:
            glib.write_to_textbox(state["textbox"], "Point selected is outside the graph")
def plot_data():
    """
    Plots the matplotlib graph using matplotlib.axes.subplot object 
    """
    if state["data"]:
        if state["plotted"]:
            glib.write_to_textbox(state["textbox"], "Data is already plotted")
        else:
            canvas, figure, subplot = glib.create_figure(state["figure"], choose_point, 800, 400)
            x_axis, y_axis = state["data"]
            subplot.plot(x_axis, y_axis, label='Intensity')
            subplot.set_xlabel("Binding Energy(eV)")
            subplot.set_ylabel("Intensity (Arbitrary Units)")
            subplot.set_title("Matplot")
            canvas.draw()
            state["canvas"] = canvas
            state["plotted"] = True
    else:
        glib.write_to_textbox(state["textbox"], "Data is not loaded. Load data first")
def update_plot(canvas, data):
    """
    Updates the plot after the points have been loaded
    Coded in reference to 
    https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.add_subplot
    """
    canvas.figure.clear()
    x_data, y_data = data
    subplot = canvas.figure.add_subplot()
    subplot.plot(x_data, y_data, label="Intensity")
    subplot.set_xlabel("Binding Energy(eV)")
    subplot.set_ylabel("Intensity (Arbitrary Units)")
    subplot.set_title("Matplot")
    subplot.legend()
    canvas.draw()
def calculate_parameters(x_1, y_1, x_2, y_2):
    """
    Calculates the slope and intercept values from two given points

    :param x and y values of two points
    """
    slope = float((y_2 - y_1) / (x_2 - x_1))
    intercept = float(((x_2 * y_1) - (x_1 * y_2)) / (x_2 - x_1))
    return slope, intercept
def determine_points():
    """ Produces a numpy array of values that are the y values of a line with
    the given slope and y intercept, from a list of x values. """
    point_1, point_2 = state["points"]
    slope, intercept = calculate_parameters(point_1[0], point_1[1], point_2[0], point_2[1])
    x_val, y_val = state["data"]
    return (x_val*slope) + intercept
def remove_linear():
    """
    Removes linear dependency from the graph
    """
    state["dependency"] = True
    if state["data_loaded"] and state["plotted"]:
        if not state["dependency"]:
            glib.write_to_textbox(state["textbox"], "Select two points after clicking 'Remove Linear Dependency'")
        elif len(state["points"]) != 2:
            glib.write_to_textbox(state["textbox"], "Select exactly two points.")
            reset_state_dic("points")
        else:
            line_values = determine_points()
            original_x, original_y = state["data"]
            modified_y = original_y - line_values
            state["data"] = (original_x, modified_y)
            update_plot(state["canvas"], state["data"])
            state["points"] = []  # Reset points after calculation
            state["dependency"] = False  # Reset the dependency flag
            glib.write_to_textbox(state["textbox"], "Linear dependency removed.")
    elif state["data"] and not state["plotted"]:
        glib.write_to_textbox(state["textbox"], "Please plot the data first")
    else:
        glib.write_to_textbox(state["textbox"], "Data is not loaded. Please load data first")
def intensity():
    """
    Calculates the intensity values from a given range of points
    """
    state["intensity"] = True
    if state["data_loaded"] and state["plotted"]:
        if not state["intensity"]:
            glib.write_to_textbox(state["textbox"], "Select points after clicking 'Calculate Intensities'")
            state["intensity"] = True  
        elif len(state["points"]) != 2:
            glib.write_to_textbox(state["textbox"], "Select exactly two points.")
            reset_state_dic("points")
        else:
            x_data, y_data = state["data"]
            points = state["points"]
            min_bound = min(points[0][0], points[1][0])
            max_bound = max(points[0][0], points[1][0])
            main_interval = (x_data >= min_bound) & (x_data <= max_bound)
            x_interval = x_data[main_interval]
            y_interval = y_data[main_interval]
            if len(x_interval) == 0 or len(y_interval) == 0:
                glib.write_to_textbox(state["textbox"], "Error, Failed to select a valid interval. Please try again.")
            else:
                intensity_value = np.trapz(y_interval, x_interval)
                glib.write_to_textbox(state["textbox"], f"Intensity: {intensity_value:.2f}")
                state["intensity"] = False 
                state["points"] = []
    elif state["data"] and not state["plotted"]:
        glib.write_to_textbox(state["textbox"], "Please plot the data first")
    else:
        glib.write_to_textbox(state["textbox"], "Data is not loaded. Please load data first")
def save_figure():
    """
    Saves the figure as a png file into the destination
    """
    if not state["data"]:
        glib.write_to_textbox(state["textbox"], "Please load data first")
    elif state["data"] and not state["plotted"]:
        glib.write_to_textbox(state["textbox"], "Please plot the data first")
    else:
        try:
            path = glib.open_save_dialog("Save your graph")
        except Exception as e:
            glib.write_to_textbox(state["textbox"], "Unable to save file. Please try again")
        else:
            path += ".png"
            canvas = state["canvas"]
            canvas.figure.savefig(path, format = "png")
            glib.write_to_textbox(state["textbox"], f"File saved to {path}")
def main():
    """
    Creates a user interface that contains an interactive figure and a textbox.
    A plot based on data received as parameters is drawn into the figure.
    """
    main_window = glib.create_window("matplot")
    button_frame = glib.create_frame(main_window, side=glib.TOP)
    figure_frame = glib.create_frame(main_window, side=glib.BOTTOM)
    state["figure"] = figure_frame
    state["textbox"] = glib.create_textbox(figure_frame, width= 80, height= 10)
    glib.create_button(button_frame, "Load Data", open_folder)
    glib.create_button(button_frame, "Plot Data", plot_data)
    glib.create_button(button_frame, "Remove Linear Dependency", remove_linear)
    glib.create_button(button_frame, "Calculate Intensities", intensity)
    glib.create_button(button_frame, "Save Figure", save_figure)
    glib.create_button(button_frame, "quit", glib.quit)
    glib.start()
if __name__ == "__main__":
    main()
 