import json
import requests
import datetime
import os
from fastapi import FastAPI
import gradio as gr
from modules import shared, scripts, script_callbacks, generation_parameters_copypaste
from PIL import Image
from io import BytesIO

dir = scripts.basedir()
embed_url = "http://127.0.0.1:7860/"
webhook_content = ""
webhook_title = "Current Stable Diffusion URL"
webhook_description = "The current url is:"
webhook_footer = "Last updated"
webhook_avatar_name = "Gradio"
webhook_avatar_url = "https://gradio.app/assets/img/logo.png"
webhook_color = 15376729
webhook_image_content = ""
webhook_image_description = "Generated by: "
webhook_image_footer = "Generated at"
webhook_image_avatar_name = "Gradio"
webhook_image_avatar_url = "https://gradio.app/assets/img/logo.png"
webhook_image_color = 15376729
webhook_image_prompt = False
share_warn = False
refresh_symbol = '\U0001f504'  # 🔄
nl = "\n"


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def init(demo: gr.Blocks, app: FastAPI):
    if not shared.cmd_opts.api:
        print(bcolors.ERROR +
              "ERR: API isn't enabled (no --api flag)." + bcolors.ENDC)
        return
    if shared.cmd_opts.share:
        post_share_url(demo)
        global embed_url
        embed_url = demo.share_url
    else:
        global share_warn
        if not share_warn:
            print(bcolors.WARNING +
                  "WRN: No public url to share (no --share flag)" + bcolors.ENDC)
            share_warn = True


def send_new_message(embed: dict, has_image: bool = False):
    """
    Sends a new message to the webhook
    args:
        embed: the embed to send
    """
    if has_image:
        response = requests.post(shared.opts.webhook_share_url,
                                 json=embed, params={"wait": True})
    else:
        response = requests.post(shared.opts.webhook_url,
                             json=embed, params={"wait": True})
        message_id = response.json()['id']
        with open(dir + '\webhook_message.json', 'w') as f:
            json.dump(message_id, f)


def post_share_url(demo: gr.Blocks):
    if shared.opts.webhook_url != "":
        share_url = demo.share_url
        try:
            with open(dir + '\webhook_message.json', 'r') as f:
                message_id = json.load(f)
        except:
            message_id = None
        title_url = ""
        if shared.opts.webhook_title_url:
            title_url = share_url
        embed = generate_embed()
        embed['embeds'][0]['url'] = title_url
        embed['embeds'][0]['description'] += '\n' + share_url  # type: ignore
        if not shared.opts.webhook_edit_message and message_id is not None:
            requests.delete(f'{shared.opts.webhook_url}/messages/{message_id}')
            message_id = None
            send_new_message(embed)
            return
        r = requests.patch(
            f'{shared.opts.webhook_url}/messages/{message_id}', json=embed, params={"wait": True})
        if r.status_code != 200:
            send_new_message(embed)
    else:
        print(bcolors.WARNING +
              "WRN: No webhook url was provided to share the web UI." + bcolors.ENDC)


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as discord_webhook:
        with gr.Tab(label="URL Embed"):
            with gr.Row().style(equal_height=False):
                with gr.Column(variant='panel'):
                    gr.HTML(
                        value="Edit the embed posted to Discord that shares the public URL")
                    _webhook_content = gr.Textbox(
                        value=webhook_content, interactive=True, label="Content", type="text")
                    _webhook_title = gr.Textbox(
                        value=webhook_title, interactive=True, label="Title")
                    _webhook_description = gr.Textbox(
                        value=webhook_description, interactive=True, label='Description')
                    _webhook_footer = gr.Textbox(
                        value=webhook_footer, interactive=True, label='Footer Message')
                    _webhook_avatar_name = gr.Textbox(
                        value=webhook_avatar_name, interactive=True, label='Avatar Name')
                    _webhook_avatar_url = gr.Textbox(
                        value=webhook_avatar_url, interactive=True, label='Avatar Image URL')
                    _webhook_color = gr.ColorPicker(
                        value="#" + format(webhook_color, 'X'), interactive=True, label='Color')
                with gr.Column():
                    with gr.Column():
                        _output = gr.HTML(
                            value=f"Change a value or press the {refresh_symbol} button to generate a preview of the embed.")
                    with gr.Column():
                        gr.Button(value=refresh_symbol, variant="primary").click(
                            fn=generate_html, outputs=[_output])
            _webhook_content.change(fn=save_content, inputs=[
                                    _webhook_content], outputs=[_output])
            _webhook_title.change(fn=save_title, inputs=[
                                  _webhook_title], outputs=[_output])
            _webhook_description.change(fn=save_desciption, inputs=[
                                        _webhook_description], outputs=[_output])
            _webhook_footer.change(fn=save_footer, inputs=[
                                   _webhook_footer], outputs=[_output])
            _webhook_avatar_name.change(fn=save_avatar_name, inputs=[
                                        _webhook_avatar_name], outputs=[_output])
            _webhook_avatar_url.change(fn=save_avatar_url, inputs=[
                                       _webhook_avatar_url], outputs=[_output])
            _webhook_color.change(fn=save_color, inputs=[
                                  _webhook_color], outputs=[_output])
        with gr.Tab(label="Share Embed"):
            with gr.Row().style(equal_height=False):
                with gr.Column(variant='panel'):
                    gr.HTML(
                        value="Edit the embed posted to Discord that shares the generated images")
                    _webhook_image_content = gr.Textbox(
                        value=webhook_image_content, interactive=True, label="Content", type="text")
                    _webhook_image_description = gr.Textbox(
                        value=webhook_image_description, interactive=True, label='Description')
                    _webhook_image_footer = gr.Textbox(
                        value=webhook_image_footer, interactive=True, label='Footer Message')
                    _webhook_image_avatar_name = gr.Textbox(
                        value=webhook_image_avatar_name, interactive=True, label='Avatar Name')
                    _webhook_image_avatar_url = gr.Textbox(
                        value=webhook_image_avatar_url, interactive=True, label='Avatar Image URL')
                    ''' _webhook_image_author = gr.Textbox(
                        value="", hint="Anonymous", interactive=True, label="Author") '''
                    _webhook_image_color = gr.ColorPicker(
                        value="#" + format(webhook_image_color, 'X'), interactive=True, label='Color')
                    _webhook_image_prompt = gr.Checkbox(
                        value=False, interactive=True, label="Show prompt")
                with gr.Column():
                    with gr.Column():
                        __output = gr.HTML(
                            value=f"Change a value or press the {refresh_symbol} button to generate a preview of the embed.")
                    with gr.Column():
                        gr.Button(value=refresh_symbol, variant="primary").click(
                            fn=generate_image_html, outputs=[__output])
            _webhook_image_content.change(fn=image_save_content, inputs=[
                                          _webhook_image_content], outputs=[__output])
            _webhook_image_description.change(fn=image_save_desciption, inputs=[
                                              _webhook_image_description], outputs=[__output])
            _webhook_image_footer.change(fn=image_save_footer, inputs=[
                                         _webhook_image_footer], outputs=[__output])
            _webhook_image_avatar_name.change(fn=image_save_avatar_name, inputs=[
                                              _webhook_image_avatar_name], outputs=[__output])
            _webhook_image_avatar_url.change(fn=image_save_avatar_url, inputs=[
                                             _webhook_image_avatar_url], outputs=[__output])
            _webhook_image_color.change(fn=image_save_color, inputs=[
                                        _webhook_image_color], outputs=[__output])
            ''' _webhook_image_author.change(fn=generate_image_author, inputs=[
                                         _webhook_image_author], outputs=[__output]) '''
            _webhook_image_prompt.change(fn=generate_image_prompt, inputs=[
                                         _webhook_image_prompt], outputs=[__output])
    return (discord_webhook, "Discord Webhook", "discord_webhook"),


def on_ui_settings():
    section = ('discord-webhook', "Discord Webhook")
    shared.opts.add_option("webhook_edit_message", shared.OptionInfo(
        False, "Edit last message sent", section=section))
    shared.opts.add_option("webhook_title_url", shared.OptionInfo(
        True, "Embed title is also public url", section=section))
    shared.opts.add_option("webhook_share_all", shared.OptionInfo(
        False, "Share ALL generated images", section=section))
    shared.opts.add_option("webhook_url", shared.OptionInfo(
        "", "Webhook to share the public url", section=section))
    shared.opts.add_option("webhook_share_url", shared.OptionInfo(
        "", "Webhook to share the generated images", section=section))


############################################
# Support functions for save embed
############################################
def save_content(input):
    return save_embed(input, "content")


def save_title(input):
    return save_embed(input, "title")


def save_desciption(input):
    return save_embed(input, "description")


def save_footer(input):
    return save_embed(input, "footer")


def save_avatar_name(input):
    return save_embed(input, "avatar_name")


def save_avatar_url(input):
    return save_embed(input, "avatar_url")


def save_color(input):
    return save_embed(input, "color")


def image_save_content(input):
    return image_save_embed(input, "content")


def image_save_title(input):
    return image_save_embed(input, "title")


def image_save_desciption(input):
    return image_save_embed(input, "description")


def image_save_footer(input):
    return image_save_embed(input, "footer")


def image_save_avatar_name(input):
    return image_save_embed(input, "avatar_name")


def image_save_avatar_url(input):
    return image_save_embed(input, "avatar_url")


def image_save_color(input):
    return image_save_embed(input, "color")


############################################
# embed generation and saving
############################################
''' def generate_image_author(input):
    global webhook_image_author
    webhook_image_author = input
    if input == "":
        webhook_image_author = "Anonymous"
    return generate_image_html()
'''


def generate_image_prompt(input):
    global webhook_image_prompt
    webhook_image_prompt = input
    return generate_image_html()


def generate_html():
    _webhook_color = "#" + format(webhook_color, 'X')
    return f'<div class="embed_wrapper"><div class="content">{webhook_content}</div><div style="border-color: {_webhook_color}; max-width: 332px" class="embed_color"><div class="embed_text"><span class="embed_title_wrapper">{webhook_title}</span><div class="embed_description_wrapper"><div class="embed_text desc">{webhook_description + nl}<a href="{embed_url}" style="color: #328DD2" target="_blank">{embed_url}</a></div></div></div></div></div>'


def generate_image_html(prompt=None):
    _webhook_image_color = "#" + format(webhook_image_color, 'X')
    desc = prompt
    return f'<div class="embed_wrapper"><div class="content">{webhook_image_content}</div><div style="border-color: {_webhook_image_color}; max-width: 332px" class="embed_color"><div class="embed_text"><span class="embed_title_wrapper">{webhook_image_description + webhook_image_author}</span><div class="embed_description_wrapper"><div class="embed_text desc">{desc}<a href="{embed_url}" style="color: #328DD2" target="_blank">{embed_url}</a></div></div></div></div></div>'


def save_embed(input, key):
    """Save each embed's content in a global variable. 
    Then generate the html and write it to the file."""
    global webhook_content, webhook_title, webhook_description, webhook_footer, webhook_avatar_name, webhook_avatar_url, webhook_color
    if key == "content":
        webhook_content = input
    elif key == "title":
        webhook_title = input
    elif key == "description":
        webhook_description = input
    elif key == "footer":
        webhook_footer = input
    elif key == "avatar_name":
        webhook_avatar_name = input
    elif key == "avatar_url":
        webhook_avatar_url = input
    elif key == "color":
        webhook_color = int(input[1:], 16)
    write_embed()
    return generate_html()


def image_save_embed(input, key):
    """Save each embed's content in a global variable. 
    Then generate the html and write it to the file."""
    global webhook_image_content, webhook_image_description, webhook_image_footer, webhook_image_avatar_name, webhook_image_avatar_url, webhook_image_color
    if key == "content":
        webhook_image_content = input
    elif key == "description":
        webhook_image_description = input
    elif key == "footer":
        webhook_image_footer = input
    elif key == "avatar_name":
        webhook_image_avatar_name = input
    elif key == "avatar_url":
        webhook_image_avatar_url = input
    elif key == "color":
        webhook_image_color = int(input[1:], 16)
    write_image_embed()
    return generate_image_html()


def generate_embed():
    return {"content": webhook_content, "embeds": [{"title": webhook_title, "url": "", "description": webhook_description, "color": webhook_color, "footer": {"text": webhook_footer}, "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}], "username": webhook_avatar_name, "avatar_url": webhook_avatar_url, "attachments": []}


def generate_image_embed(url):
    webhook_image_author = requests.get(url + "/user/").text
    return {"content": webhook_image_content, "embeds": [{"title": "", "url": "", "description": webhook_image_description, "color": webhook_image_color, "author": {"name": webhook_image_description + webhook_image_author}, "footer": {"text": webhook_image_footer}, "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}], "username": webhook_image_avatar_name, "avatar_url": webhook_avatar_url, "attachments": []}


def write_embed():
    """Write the embed to the file."""
    with open(dir + '\webhook_embed.json', 'w') as f:
        json.dump(generate_embed(), f)


def write_image_embed():
    """Write the embed to send image to the file."""
    with open(dir + '\webhook_image_embed.json', 'w') as f:
        json.dump(generate_image_embed(), f)


def load_embed():
    global webhook_content, webhook_title, webhook_description, webhook_footer, webhook_avatar_name, webhook_avatar_url, webhook_color
    try:
        with open(dir + '\webhook_embed.json', 'r') as f:
            embed = json.load(f)
            webhook_content = embed["content"]
            webhook_title = embed["embeds"][0]["title"]
            webhook_description = embed["embeds"][0]["description"]
            webhook_footer = embed["embeds"][0]["footer"]["text"]
            webhook_avatar_name = embed["username"]
            webhook_avatar_url = embed["avatar_url"]
            webhook_color = embed["embeds"][0]["color"]
    except FileNotFoundError:
        write_embed()
    except:
        # Change the name of the file to .old
        try:
            os.rename(dir + '\webhook_embed.json',
                      dir + '\webhook_embed.json.old')
        except FileExistsError:
            os.remove(dir + '\webhook_embed.json.old')
            os.rename(dir + '\webhook_embed.json',
                      dir + '\webhook_embed.json.old')
        write_embed()


# TODO:
# Support for embed.
# Transmission of multiple images.
# Compression for images over 8MB.
def post_image(data: list):
    """
    args:
        data: [string, {str: str}, [{str: str}], string]
    """
    print(data)
    if data[0] is None:
        print("[discord_webhook] No image data to share")
        return
    if shared.opts.webhook_share_url is None:
        print(bcolors.WARNING +
              "ERR: No webhook to share the image was provided." + bcolors.ENDC)
        return
    print("[discord_webhook] Converting image...")
    # img4post PIL.Image: convert data[0] to PIL.Image
    img4post = generation_parameters_copypaste.image_from_url_text(data[0])
    # PIL.Image -> bytes
    img_bytes = BytesIO()
    img4post.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    print("[discord_webhook] Converting image... (done)")

    # Create embed
    try:
        with open(dir + '\webhook_image_embed.json', 'r') as f:
            message_id = json.load(f)
    except:
        message_id = None
    embed = generate_image_embed(data[1])
    ######
    # Image attachment for send_new_message is not implemented (wip)
    ######
    # if not shared.opts.webhook_edit_message and message_id is not None:
    #     requests.delete(f'{shared.opts.webhook_share_url}/messages/{message_id}')
    #     message_id = None
    #     send_new_message(embed)
    #     return

    # Send to Discord
    print("[discord_webhook] Sending to Discord...")
    send_new_message(embed, True)
    r = requests.post(
        f'{shared.opts.webhook_share_url}', json=embed, params={"wait": True}, files={"file.png": img_bytes})
    if r.status_code != 200:
        # send_new_message(embed)
        print(f"Error: {r.status_code} {r.reason}")
        return
    else:
        print("[discord_webhook] Sending to Discord... (done)")


load_embed()

gallery = None


class Script(scripts.Script):

    def title(self):
        return "Discord Webhook"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def after_component(self, component, **kwargs):
        global gallery
        src_imgdata = None
        if isinstance(component, gr.Gallery):
            if component.elem_id in {'txt2img_gallery', 'img2img_gallery'}:
                gallery = component
                # print("[discord_webhook] Found gallery: " + component.elem_id)
        if kwargs.get("value") == "Send to extras":
            # print("[discord_webhook] gallery.elem_id: " + gallery.elem_id)
            discord_button = gr.Button(
                "Post to Discord", elem_id=f"discord_button")
            discord_button.click(
                fn=post_image,
                inputs=gallery,
                outputs=src_imgdata,
                _js="image_and_url"
            )

    def ui(self, is_img2img):
        return []


script_callbacks.on_app_started(init)
script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
# Callback for all generated images

# TODO:
# Add placeholder (hints) to textboxes
# Button to send a new embed
# - Button to send a preview image embed
#    - Find a suitable placeholder image (Gradio Icon?)
# Customize README
# Add tooltips to settings
# Embed customizer for sharing images
# Option to share all generated images - Off by default
# Use api for username ./user/

# WORKING ON:
# Embed visualizer - 1/2 (Share Url Half Done), (Display Footer Message, Avatar Name, Avatar Url, Content(Message) DONE)
# Button to share generated images - Share grid and first 3 if no image is selected

# DONE:
# Share public url to Discord
# Make repo public
# Button to generate new preview
# Warning when no webhook_share_url is provided
