import gradio as gr

def generate_images(fabric_prompt, num_images, categories, width, height, steps, guidance, seed, timestep_to_start_cfg):
    # Here, you would implement the logic to generate images
    generated_images = [f"generated_image_{i}.jpg" for i in range(num_images)]  # Example image paths
    return generated_images

# Define the layout
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            fabric_prompt = gr.Textbox(label="fabric_prompt", value="single jersey")
            categories = gr.CheckboxGroup(
                label="服装品类",
                choices=["T恤", "小衫", "连衣裙", "半裙", "衬衫", "Polo衫", "风衣", "裤子", "卫衣", "夹克"],
                value=["T恤", "Polo衫", "风衣"],
            )
            num_images = gr.Slider(label="Num images", minimum=1, maximum=10, value=1)
            width = gr.Slider(label="Width", minimum=512, maximum=2048, value=768)
            height = gr.Slider(label="Height", minimum=512, maximum=2048, value=1024)
            steps = gr.Slider(label="Steps", minimum=1, maximum=100, value=40)
            guidance = gr.Slider(label="Guidance", minimum=1, maximum=500, value=4)
            seed = gr.Slider(label="Seed (-1 for random)", minimum=-1, maximum=1000, value=-1)
            timestep_to_start_cfg = gr.Slider(label="timestep_to_start_cfg", minimum=1, maximum=500, value=1)
            generate_button = gr.Button(value="Generate", elem_id="generate_button")
        
        with gr.Column():
            # Correct way to create a Gallery component without style()
            output_image = gr.Gallery(label="Generated images", elem_id="generated_images", columns=5)
            download_button = gr.Button(value="Download Image")

    # Set button actions
    generate_button.click(
        generate_images, 
        inputs=[fabric_prompt, num_images, categories, width, height, steps, guidance, seed, timestep_to_start_cfg], 
        outputs=[output_image]
    )

# Launch Gradio app, binding to 0.0.0.0 and specifying the port
demo.launch(server_name="0.0.0.0", server_port=20004)
