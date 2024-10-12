def test_page():
    pass

    # First, import the elements you need

    from streamlit_elements import elements, mui, html

    # Create a frame where Elements widgets will be displayed.
    #
    # Elements widgets will not render outside of this frame.
    # Native Streamlit widgets will not render inside this frame.
    #
    # elements() takes a key as parameter.
    # This key can't be reused by another frame or Streamlit widget.

#     with elements("style_mui_sx"):

#         # For Material UI elements, use the 'sx' property.
#         #
#         # <Box
#         #   sx={{
#         #     bgcolor: 'background.paper',
#         #     boxShadow: 1,
#         #     borderRadius: 2,
#         #     p: 2,
#         #     minWidth: 300,
#         #   }}
#         # >
#         #   Some text in a styled box
#         # </Box>

#         mui.Box(
#             "Some text in a styled box",
#             sx={
#                 "bgcolor": "background.paper",
#                 "boxShadow": 1,
#                 "borderRadius": 2,
#                 "p": 2,
#                 "minWidth": 300,
#             }
#         )
        
#     with elements("style_elements_css"):

#         # For any other element, use the 'css' property.
#         #
#         # <div
#         #   css={{
#         #     backgroundColor: 'hotpink',
#         #     '&:hover': {
#         #         color: 'lightgreen'
#         #     }
#         #   }}
#         # >
#         #   This has a hotpink background
#         # </div>

#         html.div(
#             "This has a hotpink background",
#             css={
#                 "backgroundColor": "hotpink",
#                 "&:hover": {
#                     "color": "lightgreen"
#                 }
#             }
#         )        
        
    import streamlit as st

    with elements("callbacks_retrieve_data"):

        # Some element allows executing a callback on specific event.
        #
        # const [name, setName] = React.useState("")
        # const handleChange = (event) => {
        #   // You can see here that a text field value
        #   // is stored in event.target.value
        #   setName(event.target.value)
        # }
        #
        # <TextField
        #   label="Input some text here"
        #   onChange={handleChange}
        # />

        # Initialize a new item in session state called "my_text"
        if "my_text" not in st.session_state:
            st.session_state.my_text = ""

        # When text field changes, this function will be called.
        # To know which parameters are passed to the callback,
        # you can refer to the element's documentation.
        def handle_change(event):
            st.session_state.my_text = event.target.value

        # Here we display what we have typed in our text field
        mui.Typography(st.session_state.my_text)

        # And here we give our 'handle_change' callback to the 'onChange'
        # property of the text field.
        mui.TextField(label="Input some text here", onChange=handle_change)        
        
    with elements("callbacks_sync"):

        # If you just want to store callback parameters into Streamlit's session state
        # like above, you can also use the special function sync().
        #
        # When an onChange event occurs, the callback is called with an event data object
        # as argument. In the example below, we are synchronizing that event data object with
        # the session state item 'my_event'.
        #
        # If an event passes more than one parameter, you can synchronize as many session state item
        # as needed like so:
        # >>> sync("my_first_param", "my_second_param")
        #
        # If you want to ignore the first parameter of an event but keep synchronizing the second,
        # pass None to sync:
        # >>> sync(None, "second_parameter_to_keep")

        from streamlit_elements import sync

        if "my_event" not in st.session_state:
            st.session_state.my_event = None

        if st.session_state.my_event is not None:
            text = st.session_state.my_event.target.value
        else:
            text = ""

        mui.Typography(text)
        mui.TextField(label="Input some text here", onChange=sync("my_event"))        
        
    with elements("dashboard"):

        # You can create a draggable and resizable dashboard using
        # any element available in Streamlit Elements.

        from streamlit_elements import dashboard

        # First, build a default layout for every element you want to include in your dashboard

        layout = [
            # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
            dashboard.Item("first_item", 0, 0, 2, 2),
            dashboard.Item("second_item", 2, 0, 2, 2, isDraggable=False, moved=False),
            dashboard.Item("third_item", 0, 2, 1, 1, isResizable=False),
        ]

        # Next, create a dashboard layout using the 'with' syntax. It takes the layout
        # as first parameter, plus additional properties you can find in the GitHub links below.

        with dashboard.Grid(layout):
            mui.Paper("First item", key="first_item")
            mui.Paper("Second item (cannot drag)", key="second_item")
            mui.Paper("Third item (cannot resize)", key="third_item")

        # If you want to retrieve updated layout values as the user move or resize dashboard items,
        # you can pass a callback to the onLayoutChange event parameter.

        def handle_layout_change(updated_layout):
            # You can save the layout in a file, or do anything you want with it.
            # You can pass it back to dashboard.Grid() if you want to restore a saved layout.
            print(updated_layout)

        with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
            mui.Paper("First item", key="first_item")
            mui.Paper("Second item (cannot drag)", key="second_item")
            mui.Paper("Third item (cannot resize)", key="third_item")        
            
            
    with elements("monaco_editors"):

        # Streamlit Elements embeds Monaco code and diff editor that powers Visual Studio Code.
        # You can configure editor's behavior and features with the 'options' parameter.
        #
        # Streamlit Elements uses an unofficial React implementation (GitHub links below for
        # documentation).

        from streamlit_elements import editor
        from streamlit_elements import lazy

        if "content" not in st.session_state:
            st.session_state.content = "Default value"

        mui.Typography("Content: ", st.session_state.content)

        def update_content(value):
            st.session_state.content = value

        editor.Monaco(
            height=300,
            defaultValue=st.session_state.content,
            onChange=lazy(update_content)
        )

        mui.Button("Update content", onClick=sync())

        editor.MonacoDiff(
            original="Happy Streamlit-ing!",
            modified="Happy Streamlit-in' with Elements!",
            height=300,
        )            
        

    with elements("nivo_charts"):

        # Streamlit Elements includes 45 dataviz components powered by Nivo.

        from streamlit_elements import nivo

        DATA = [
            { "taste": "fruity", "chardonay": 93, "carmenere": 61, "syrah": 114 },
            { "taste": "bitter", "chardonay": 91, "carmenere": 37, "syrah": 72 },
            { "taste": "heavy", "chardonay": 56, "carmenere": 95, "syrah": 99 },
            { "taste": "strong", "chardonay": 64, "carmenere": 90, "syrah": 30 },
            { "taste": "sunny", "chardonay": 119, "carmenere": 94, "syrah": 103 },
        ]

        with mui.Box(sx={"height": 500}):
            nivo.Radar(
                data=DATA,
                keys=[ "chardonay", "carmenere", "syrah" ],
                indexBy="taste",
                valueFormat=">-.2f",
                margin={ "top": 70, "right": 80, "bottom": 40, "left": 80 },
                borderColor={ "from": "color" },
                gridLabelOffset=36,
                dotSize=10,
                dotColor={ "theme": "background" },
                dotBorderWidth=2,
                motionConfig="wobbly",
                legends=[
                    {
                        "anchor": "top-left",
                        "direction": "column",
                        "translateX": -50,
                        "translateY": -40,
                        "itemWidth": 80,
                        "itemHeight": 20,
                        "itemTextColor": "#999",
                        "symbolSize": 12,
                        "symbolShape": "circle",
                        "effects": [
                            {
                                "on": "hover",
                                "style": {
                                    "itemTextColor": "#000"
                                }
                            }
                        ]
                    }
                ],
                theme={
                    "background": "#FFFFFF",
                    "textColor": "#31333F",
                    "tooltip": {
                        "container": {
                            "background": "#FFFFFF",
                            "color": "#31333F",
                        }
                    }
                }
            )        
            
            
    import streamlit as st
    from streamlit_super_slider import st_slider

    st.title("Streamlit Super Slider Example")

    min_value = 0
    max_value = 100
    default_value = 50

    # Use the Streamlit Super Slider component
    slider_value = st_slider(min_value, max_value, default_value)

    st.write("Slider with range")
    value = st_slider(values={0: "zero", 10:'10', 25:'25', max_value: "max"}, key="my_slider2" ,dots=False)
    st.write("Slider custom values from dictionary and steps")
    value = st_slider(values={0: "zero", 10:'10', 20:'30', 90:'90', max_value: "max"}, key="my_slider2_steps" ,dots=False, steps=10)
    st.write("Slider custom values from dictionary, steps and dots")
    value = st_slider(values={0: "zero", 10:'10', 20:'30', 90:'90', max_value: "max"}, key="my_slider2_dots_steps" ,dots=True, steps=10)
    st.write("Slider with custom values from list")
    value = st_slider(values=[0,100,350,34560], key="my_slider3")

    st.write(f"Selected value: {slider_value}")
