import Eto.Drawing as drawing
import Eto.Forms as forms
import Rhino
import scriptcontext as sc
import math

class SimpleDrawable(forms.Drawable):
    def __init__(self, state):
        self.BackgroundColor = drawing.Color.FromArgb(13, 13, 13) if state else drawing.Color.FromArgb(242, 242, 242)  # initialize the window background color based on the state
        self.min_width = 50  # set the minimum width for the button
        self.max_width = 300  # set the maximum width for the button
        self.reference_width = 500  # reference width when the button is at normal size
        self.padding = 20  # define padding around the button
        self._hover = False  # flag to check if the mouse is hovering over the button
        self._state = state  # initialize the state based on the passed argument
        self._is_transitioning = False  # flag to track if a transition is in progress

        # set up the timer for smooth transitions
        self._timer = forms.UITimer()
        self._timer.Interval = 0.005  # update every 5 milliseconds
        self._timer.Elapsed += self.on_timer_tick
        self._transition_step = 0  # track the progress of the transition
        self._transition_duration = 25  # total steps for the transition

    def f(self, x, ref, min_size, max_size):
        # logarithmic scaling for smoother initial transitions and subtle growth later
        scale_factor = 1 + math.log1p(x / ref)  # use log1p for scaling
        scaled_size = scale_factor * min_size
        return max(min_size, min(max_size, scaled_size))  # keep the size within the min and max bounds

    def OnPaint(self, e):
        # calculate the rectangle size
        rect_width = self.f(self.Width - 2 * self.padding, self.reference_width, self.min_width, self.max_width)
        rect_height = rect_width / 2  # height is always half of the width
        corner_radius = rect_height / 2  # set the corner radius based on the rectangle height

        # calculate the center position
        rect_x = (self.Width - rect_width) / 2
        rect_y = (self.Height - rect_height) / 2
        
        # create the rounded rectangle path
        rect = drawing.RectangleF(rect_x, rect_y, rect_width, rect_height)
        path = drawing.GraphicsPath.GetRoundRect(rect, corner_radius)
        pen = drawing.Pen(drawing.Color.FromArgb(13, 13, 13), 0)  # create a pen with the background color

        # determine colors based on the state and transition
        t = self._transition_step / self._transition_duration
        if self._state:
            e.Graphics.FillPath(drawing.Color.FromArgb(242, 242, 242), path)  # fill the path with the alternate color
            circle_color = drawing.Color.FromArgb(13, 13, 13)  # set the circle color
        else:
            e.Graphics.FillPath(drawing.Color.FromArgb(13, 13, 13), path)  # fill the path with the background color
            circle_color = drawing.Color.FromArgb(242, 242, 242)  # set the circle color

        e.Graphics.DrawPath(pen, path)  # draw the path with the pen

        gap = rect_height * 0.15  # set 15% of the button's height as gap
        circle_diameter = corner_radius * 1.5  # adjust multiplier to control the circle size
        circle_radius = circle_diameter / 2  # calculate the circle radius

        if self._hover and not self._is_transitioning:  # adjust size only when not transitioning
            circle_diameter *= 1.1  # enlarge the circle slightly on hover
            circle_radius = circle_diameter / 2  # recalculate radius

        if self._state:
            circle_center_x = rect_x + (gap + circle_radius)  # position the circle on the left
        else:
            circle_center_x = (rect_x + rect_width) - (gap + circle_radius)  # position the circle on the right

        # draw the circle
        e.Graphics.FillEllipse(circle_color, (circle_center_x - circle_radius), ((rect_y + rect_height / 2) - circle_radius), circle_diameter, circle_diameter)

    def on_timer_tick(self, sender, e):
        # gradually adjust the background color
        t = self._transition_step / self._transition_duration
        if self._state:
            # transition from white to black
            r = int(242 - (242 - 13) * t)
            g = int(242 - (242 - 13) * t)
            b = int(242 - (242 - 13) * t)
        else:
            # transition from black to white
            r = int(13 + (242 - 13) * t)
            g = int(13 + (242 - 13) * t)
            b = int(13 + (242 - 13) * t)

        self.BackgroundColor = drawing.Color.FromArgb(r, g, b)  # update the background color
        
        self._transition_step += 1  # advance the transition step
        if self._transition_step > self._transition_duration:
            self._timer.Stop()  # stop the timer when the transition is complete
            self._is_transitioning = False  # mark the end of the transition

        self.Invalidate()  # repaint during the transition

    def OnMouseMove(self, e):
        # check if the mouse is within the button's bounds
        rect_width = self.f(self.Width - 2 * self.padding, self.reference_width, self.min_width, self.max_width)
        rect_height = rect_width / 2
        rect_x = (self.Width - rect_width) / 2
        rect_y = (self.Height - rect_height) / 2
        
        rect = drawing.RectangleF(rect_x, rect_y, rect_width, rect_height)
        
        was_hover = self._hover  # store previous hover state
        self._hover = rect.Contains(e.Location)  # update hover state based on mouse position

        if self._hover != was_hover and not self._is_transitioning:  # only invalidate if not in transition
            self.Invalidate()

    def OnMouseEnter(self, e):
        self.OnMouseMove(e)  # update hover state when the mouse enters the button

    def OnMouseLeave(self, e):
        self._hover = False  # reset hover state when the mouse leaves the button
        if not self._is_transitioning:  # Only invalidate if not in transition
            self.Invalidate()

    def OnMouseDown(self, e):
        if e.Buttons == forms.MouseButtons.Primary and self._hover and not self._is_transitioning:
            self._state = not self._state  # toggle the state
            self._transition_step = 0  # reset the transition step
            self._is_transitioning = True  # mark the start of a transition
            self._timer.Start()  # start the transition timer
            self.Invalidate()

    def OnMouseUp(self, e):
        pass  # nothing to do here, but we still need to define it

class SimpleDialog(forms.Dialog[bool]):
    def __init__(self):
        # initialize the dialog window
        self.WindowStyle = forms.WindowStyle.None  # no borders, because who needs those?
        self.MovableByWindowBackground = True  # let the user move the window by dragging the background
        self.Size = drawing.Size(225, 275)  # set the size of the window
        self.MinimumSize = drawing.Size(150, 150)  # set a minimum size to keep things looking good
        self.Resizable = True  # allow the window to be resized

        # load the drawing class
        self.drawable = SimpleDrawable(True)  # start with the button in the True state
        self.Content = self.drawable  # set the content of the dialog to the drawable
        
        # set up the close event for the Esc key
        self.KeyDown += self.on_key_down

    def on_key_down(self, sender, e):
        if e.Key == forms.Keys.Escape:
            self.Close(False)  # close the dialog when Esc is pressed

# define function to call the dialog box
def ShowDialogBox():
    dialog = SimpleDialog()  # create the dialog
    rc = Rhino.UI.EtoExtensions.ShowSemiModal(
        dialog,
        sc.doc.ActiveDoc,
        Rhino.UI.RhinoEtoApp.MainWindow
    )  # show the dialog modally

if __name__ == "__main__":
    ShowDialogBox()  # run the dialog if this script is executed
