# kimcad
Architectural , CAD-like Drawing for Blender

This is a control-line oriented drawing tool for walls, rafters and other architecural elements. You add Elemts by drawing 'Rubber Band' - Lines or Polylines. It supports the Blender Snap Settings.
It supports Constraints, like delta-values, angles and length of Elements, while drawing them.

this addon is in pre-alpha stage. Mostly technical demonstration.

![kim_rubberband-1](https://user-images.githubusercontent.com/130235043/230829473-55296643-305e-4eb2-8875-4ca57dce9603.jpg)


### Usage
Architectural Elements can be added through two ways: 
1. Add -> Mesh -> Kim Parts (Beams, Rafters, simple Walls)
2. Workspace Tools, until now adding simple walls are implemented

to 1. the Elements are added at the Pivot-Point with a initial size. For example the wall is 2m long and has a predefined height

to 2.
Here you can begin drawing a polyline with Left-Mouse-Click and end it again with Left-Mouse. The Wall follows this path (centered). The Path can be extended while drawing with pressing E before the next Click. ESC cancels the drawing.
Holding SHIFT will constraint the path to 90 degree angles.

#### Constraints
the path can be constrain to delta X and Y Values, angle and/ or length. Just enter the Values in the Fields. Angle and Length can be combined by selecting the '+' Button between them.

#### Snaps
