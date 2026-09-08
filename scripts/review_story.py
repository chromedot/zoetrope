#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, ListView, ListItem, Label, TextArea, Button, Static
from textual.reactive import reactive
from textual.message import Message
import os
import glob
import subprocess
import sys
from story_manager import StoryManager

class SceneItem(ListItem):
    """A list item representing a scene."""
    def __init__(self, scene_data, index):
        super().__init__()
        self.scene_data = scene_data
        self.index = index

    def update_label(self):
        status_icon = "🔒" if self.scene_data.get('status') == 'locked' else "🎲"
        if self.children:
            self.children[0].update(f"{self.scene_data['scene']}. {status_icon} {self.scene_data['description'][:30]}...")

    def compose(self) -> ComposeResult:
        status_icon = "🔒" if self.scene_data.get('status') == 'locked' else "🎲"
        yield Label(f"{self.scene_data['scene']}. {status_icon} {self.scene_data['description'][:30]}...")

class StoryApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 30%;
        height: 100%;
        border-right: solid green;
    }
    #editor {
        width: 70%;
        height: 100%;
        padding: 1;
    }
    .box {
        margin-bottom: 1;
        padding: 1;
        border: solid gray;
    }
    #prompt-editor {
        height: 10;
    }
    #status-label {
        color: yellow;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "save", "Save"),
    ]

    current_scene_index = reactive(None)
    monitoring_prefix = reactive(None)

    def __init__(self):
        super().__init__()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_story = os.path.join(base_dir, "stories", "geronimo.story")
        
        story_path = sys.argv[1] if len(sys.argv) > 1 else default_story
        
        if not os.path.exists(story_path):
            if len(sys.argv) <= 1 and os.path.exists("geronimo.story"):
                story_path = "geronimo.story"
        
        self.manager = StoryManager(story_path)
        self.story_scenes = self.manager.story_data
        self.poll_timer = None

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="sidebar"):
            yield Label("Scenes", classes="box")
            items = [SceneItem(scene, i) for i, scene in enumerate(self.story_scenes)]
            self.list_view = ListView(*items)
            yield self.list_view

        with ScrollableContainer(id="editor"):
            yield Label("Description:", classes="label")
            yield Static(id="desc-display", classes="box")
            
            yield Label("Prompt:", classes="label")
            yield TextArea(id="prompt-editor")
            
            with Horizontal(classes="box"):
                yield Button("Regenerate", id="btn-generate", variant="primary")
                yield Button("Lock Seed", id="btn-lock", variant="warning")
                yield Button("Open Image", id="btn-open", variant="default")
            
            yield Label("Status:", classes="label")
            yield Static(id="status-display")

        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        self.current_scene_index = event.item.index
        self.load_scene_to_editor(event.item.index)

    def load_scene_to_editor(self, index):
        scene = self.story_scenes[index]
        self.query_one("#desc-display", Static).update(scene['description'])
        self.query_one("#prompt-editor", TextArea).text = scene['prompt']
        self.update_status_display(scene)
        
        lock_btn = self.query_one("#btn-lock", Button)
        if scene.get('status') == 'locked':
            lock_btn.label = "Unlock Seed"
            lock_btn.variant = "success"
        else:
            lock_btn.label = "Lock Seed"
            lock_btn.variant = "warning"

    def update_status_display(self, scene):
        status = scene.get('status', 'draft')
        seed = scene.get('seed', 'N/A')
        img_path = scene.get('image_path', 'None')
        self.query_one("#status-display", Static).update(
            f"Status: {status}\nSeed: {seed}\nLast Prefix: {img_path}"
        )

    def on_button_pressed(self, event: Button.Pressed):
        if self.current_scene_index is None:
            return

        scene = self.story_scenes[self.current_scene_index]

        if event.button.id == "btn-generate":
            # Save prompt first
            new_prompt = self.query_one("#prompt-editor", TextArea).text
            scene['prompt'] = new_prompt
            self.manager.save_story()
            
            self.notify(f"Queueing Scene {scene['scene']}")
            try:
                seed, prefix = self.manager.generate_scene(self.current_scene_index)
                
                # Update UI to waiting state
                event.button.label = "Generating..."
                event.button.disabled = True
                self.monitoring_prefix = prefix
                
                # Start polling
                self.poll_timer = self.set_interval(1.0, self.check_generation_status)
                
                self.update_status_display(scene)
                
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        elif event.button.id == "btn-lock":
            if scene.get('status') == 'locked':
                scene['status'] = 'draft'
                event.button.label = "Lock Seed"
                event.button.variant = "warning"
            else:
                scene['status'] = 'locked'
                event.button.label = "Unlock Seed"
                event.button.variant = "success"
            
            self.manager.save_story()
            self.update_status_display(scene)
            self.list_view.children[self.current_scene_index].update_label()

        elif event.button.id == "btn-open":
            self.open_image(scene)

    def check_generation_status(self):
        if not self.monitoring_prefix:
            return

        # prefix is like "geronimo/new:HH:MM_scene..."
        # Check if file exists in output
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "output")
        
        folder, file_prefix = os.path.split(self.monitoring_prefix)
        # Search for file_prefix + "*.png"
        search_pattern = os.path.join(output_dir, folder, file_prefix + "*.png")
        files = glob.glob(search_pattern)
        
        if files:
            # File found!
            self.notify("Image Ready!", severity="information")
            
            # Stop timer
            if self.poll_timer:
                self.poll_timer.stop()
                self.poll_timer = None
            
            self.monitoring_prefix = None
            
            # Reset button
            gen_btn = self.query_one("#btn-generate", Button)
            gen_btn.label = "Regenerate"
            gen_btn.disabled = False
            
            # Refresh data to get the exact filename if needed (StoryManager stores prefix, that's fine)
            scene = self.story_scenes[self.current_scene_index]
            self.update_status_display(scene)

    def open_image(self, scene):
        prefix = scene.get('image_path')
        if not prefix:
            self.notify("No image generated yet.")
            return
            
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "output")
        
        folder, file_prefix = os.path.split(prefix)
        
        if file_prefix.lower().endswith('.png'):
            search_pattern = os.path.join(output_dir, folder, file_prefix)
        else:
            search_pattern = os.path.join(output_dir, folder, file_prefix + "*.png")
            
        files = glob.glob(search_pattern)
        
        if not files:
            self.notify(f"File not found yet (still generating?).", severity="warning")
            return
            
        files.sort(key=os.path.getmtime, reverse=True)
        latest_file = files[0]
        
        self.notify(f"Opening {os.path.basename(latest_file)}")
        subprocess.call(["xdg-open", latest_file])

if __name__ == "__main__":
    app = StoryApp()
    app.run()
