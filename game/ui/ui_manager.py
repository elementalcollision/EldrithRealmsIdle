import pygame
import os
from game.constants import (SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_COLOR, TEXT_COLOR, 
                           BUTTON_COLOR, BUTTON_HOVER_COLOR, GOLD_COLOR, PURPLE_COLOR, BLUE_COLOR)
from game.ui.components import (Button, Panel, ResourceDisplay, RacePanel, 
                               BuildingPanel, ResearchPanel, PrestigePanel, AchievementPanel, NotificationPanel, BulkPurchasePanel)

class UIManager:
    def __init__(self, screen, game_state):
        self.screen = screen
        self.game_state = game_state
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.scale_factor = 1.0
        self.font = pygame.font.SysFont('Arial', 18)
        self.title_font = pygame.font.SysFont('Arial', 24, bold=True)
        
        # Active tab
        self.tabs = ["races", "buildings", "research", "prestige", "achievements"]
        self.active_tab = "races"
        
        # Load race voxel graphics
        self.race_graphics = {}
        self.load_race_graphics()
        
        # Initialize UI components
        self.init_components()
        
        # Track mouse position for hover effects
        self.mouse_pos = (0, 0)
        
        # Active tab
        self.tabs = ["races", "buildings", "research", "prestige", "achievements"]
        self.active_tab = "races"
        
        # Autosave timer
        self.last_autosave_time = pygame.time.get_ticks()
        self.autosave_interval = 300000  # 5 minutes
        
        # Save/load dialog state
        self.show_save_dialog = False
        self.show_load_dialog = False
        self.show_export_dialog = False
        self.show_import_dialog = False
        self.show_notification_detail = False
        self.current_notification = None
        self.close_button_rect = None
        self.dialog_input_text = ""
        self.dialog_cursor_pos = 0
        
        # Window resize indicator
        self.show_resize_indicator = False
        self.resize_indicator_time = 0
        
    def load_race_graphics(self):
        """Load 8-bit voxel graphics for each race"""
        # Create placeholder graphics for each race
        # In a real implementation, these would be loaded from files
        race_colors = {
            "dwarf": (139, 69, 19),    # Brown
            "elf": (34, 139, 34),      # Green
            "human": (255, 222, 173),  # Light peach
            "goblin": (50, 205, 50),   # Lime green
            "troll": (65, 105, 225),   # Royal blue
            "shade": (138, 43, 226),   # Purple
            "deepling": (0, 191, 255), # Deep sky blue
            "dragon": (255, 69, 0),    # Red-orange
            "celestial": (255, 215, 0), # Gold
            "void_walker": (75, 0, 130) # Indigo
        }
        
        # Create directory for race graphics if it doesn't exist
        graphics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'images', 'races')
        os.makedirs(graphics_dir, exist_ok=True)
        
        # Create placeholder voxel graphics for each race
        for race_id, color in race_colors.items():
            # Create a surface for the race
            surface = pygame.Surface((64, 64), pygame.SRCALPHA)
            
            # Draw a simple voxel-style character
            # Head
            pygame.draw.rect(surface, color, (16, 8, 32, 24))
            # Eyes
            pygame.draw.rect(surface, (255, 255, 255), (22, 16, 8, 8))
            pygame.draw.rect(surface, (255, 255, 255), (34, 16, 8, 8))
            pygame.draw.rect(surface, (0, 0, 0), (24, 18, 4, 4))
            pygame.draw.rect(surface, (0, 0, 0), (36, 18, 4, 4))
            # Body
            pygame.draw.rect(surface, color, (20, 32, 24, 20))
            # Arms
            pygame.draw.rect(surface, color, (8, 32, 12, 8))
            pygame.draw.rect(surface, color, (44, 32, 12, 8))
            # Legs
            pygame.draw.rect(surface, color, (20, 52, 8, 12))
            pygame.draw.rect(surface, color, (36, 52, 8, 12))
            
            # Add race-specific details
            if race_id == "dwarf":
                # Beard
                pygame.draw.rect(surface, (139, 69, 19), (16, 32, 32, 8))
            elif race_id == "elf":
                # Pointy ears
                pygame.draw.rect(surface, color, (8, 12, 8, 8))
                pygame.draw.rect(surface, color, (48, 12, 8, 8))
            elif race_id == "troll":
                # Larger body
                pygame.draw.rect(surface, color, (16, 32, 32, 24))
            elif race_id == "shade":
                # Ghostly effect
                for y in range(8, 64, 4):
                    pygame.draw.line(surface, (200, 200, 255, 128), (16, y), (48, y), 1)
            
            # Save the surface to the race_graphics dictionary
            self.race_graphics[race_id] = surface
            
            # Save the image to a file for future use
            image_path = os.path.join(graphics_dir, f"{race_id}.png")
            pygame.image.save(surface, image_path)
    
    def update_screen_size(self, width, height):
        """Update UI components based on new screen size"""
        self.screen_width = width
        self.screen_height = height
        self.scale_factor = min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT)
        
        # Show resize indicator
        self.show_resize_indicator = True
        self.resize_indicator_time = pygame.time.get_ticks()
        
        # Reinitialize UI components with new dimensions
        self.init_components()
    
    def init_components(self):
        # Create main panels
        self.resource_panel = Panel(
            pygame.Rect(10, 10, self.screen_width - 20, 60),
            PANEL_COLOR
        )
        
        # Create bulk purchase panel in lower left corner
        bulk_purchase_width = 230  # 4 buttons * 50px + 3 * 10px spacing
        self.bulk_purchase_panel = BulkPurchasePanel(
            pygame.Rect(10, self.screen_height - 50, bulk_purchase_width, 30),
            self.game_state
        )
        
        # Create tab buttons
        self.tab_buttons = {}
        tab_width = int(120 * self.scale_factor)
        tab_height = int(30 * self.scale_factor)
        tab_y = int(120 * self.scale_factor)  # Increased from 80 to 120 to prevent overlap with level/prestige info
        for i, tab in enumerate(self.tabs):
            self.tab_buttons[tab] = Button(
                pygame.Rect(int(10 * self.scale_factor) + i * (tab_width + int(5 * self.scale_factor)), tab_y, tab_width, tab_height),
                tab.capitalize()
            )
        
        # Create content panel (below tabs)
        self.content_panel = Panel(
            pygame.Rect(int(10 * self.scale_factor), tab_y + tab_height + int(10 * self.scale_factor), 
                       self.screen_width - int(20 * self.scale_factor), 
                       self.screen_height - (tab_y + tab_height + int(20 * self.scale_factor))),
            PANEL_COLOR
        )
        
        # Create notification panel
        self.notification_panel = NotificationPanel(
            pygame.Rect(self.screen_width - int(300 * self.scale_factor), 
                       self.screen_height - int(150 * self.scale_factor), 
                       int(290 * self.scale_factor), int(140 * self.scale_factor)),
            self.game_state
        )
        
        # Create resource displays
        self.resource_displays = {}
        visible_resources = ["gold", "wood", "stone", "food", "mana", "crystal", "ancient_knowledge", "prestige_points"]
        resource_width = (self.screen_width - int(40 * self.scale_factor)) // len(visible_resources)
        for i, resource in enumerate(visible_resources):
            if resource in self.game_state.resources:
                self.resource_displays[resource] = ResourceDisplay(
                    pygame.Rect(int(20 * self.scale_factor) + i * resource_width, int(20 * self.scale_factor), 
                               resource_width - int(10 * self.scale_factor), int(40 * self.scale_factor)),
                    resource,
                    self.game_state
                )
        
        # Create content for each tab
        self.race_panels = {}
        self.building_panels = {}
        self.research_panels = {}
        self.prestige_upgrade_panels = {}
        
        # Initialize content for the active tab
        self.create_race_panels()
        self.create_building_panels()
        self.create_research_panels()
        self.create_prestige_panels()
        
        # Create save/load buttons
        button_width = 100
        button_height = 30
        self.save_button = Button(
            pygame.Rect(self.screen_width - button_width - 10, 110, button_width, button_height),
            "Save Game"
        )
        
        self.load_button = Button(
            pygame.Rect(self.screen_width - 2 * button_width - 20, 110, button_width, button_height),
            "Load Game"
        )
        
        # Create export/import save string buttons
        self.export_button = Button(
            pygame.Rect(self.screen_width - 3 * button_width - 30, 110, button_width, button_height),
            "Export Save"
        )
        
        self.import_button = Button(
            pygame.Rect(self.screen_width - 4 * button_width - 40, 110, button_width, button_height),
            "Import Save"
        )
        
        # Create prestige button
        self.prestige_button = Button(
            pygame.Rect(self.screen_width - 5 * button_width - 50, 110, button_width, button_height),
            "Prestige"
        )
        
        # Create time warp button
        self.time_warp_button = Button(
            pygame.Rect(self.screen_width - 6 * button_width - 60, 110, button_width, button_height),
            "Time Warp"
        )
        
    def create_race_panels(self):
        # Clear existing race panels
        self.race_panels = {}
        
        # Get unlocked races
        unlocked_races = [race_id for race_id, race_data in self.game_state.races.items() 
                         if race_data["unlocked"]]
        
        if not unlocked_races:
            return
            
        # Calculate panel dimensions with scaling
        panel_height = int(100 * self.scale_factor)
        panel_width = self.content_panel.rect.width - int(40 * self.scale_factor)
        columns = 2
        column_width = panel_width // columns
        
        for i, race_id in enumerate(unlocked_races):
            column = i % columns
            row = i // columns
            
            x_pos = self.content_panel.rect.x + int(20 * self.scale_factor) + column * column_width
            y_pos = self.content_panel.rect.y + int(20 * self.scale_factor) + (panel_height + int(10 * self.scale_factor)) * row
            
            # Skip if it would go off screen
            if y_pos + panel_height > self.content_panel.rect.y + self.content_panel.rect.height - int(10 * self.scale_factor):
                break
                
            panel = RacePanel(
                pygame.Rect(x_pos, y_pos, column_width - int(10 * self.scale_factor), panel_height),
                race_id,
                self.game_state
            )
            
            # Pass the race graphic to the panel if available
            if race_id in self.race_graphics:
                panel.race_graphic = self.race_graphics[race_id]
                
            self.race_panels[race_id] = panel
    
    def render_resize_indicator(self):
        """Render an indicator showing the current window size"""
        size_text = f"Window Size: {self.screen_width}x{self.screen_height} (Scale: {self.scale_factor:.2f}x)"
        text_surface = self.font.render(size_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, 30))
        
        # Draw background with transparency
        bg_rect = text_rect.inflate(20, 10)
        s = pygame.Surface((bg_rect.width, bg_rect.height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        self.screen.blit(s, bg_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), bg_rect, 1)
        
        # Draw text
        self.screen.blit(text_surface, text_rect)
    
    def create_building_panels(self):
        # Clear existing building panels
        self.building_panels = {}
        
        # Get unlocked buildings
        unlocked_buildings = [building_id for building_id, building_data in self.game_state.buildings.items() 
                             if building_data["unlocked"]]
        
        if not unlocked_buildings:
            return
            
        # Calculate panel dimensions
        panel_height = 100
        panel_width = self.content_panel.rect.width - 40
        columns = 2
        column_width = panel_width // columns
        
        for i, building_id in enumerate(unlocked_buildings):
            column = i % columns
            row = i // columns
            
            x_pos = self.content_panel.rect.x + 20 + column * column_width
            y_pos = self.content_panel.rect.y + 20 + (panel_height + 10) * row
            
            # Skip if it would go off screen
            if y_pos + panel_height > self.content_panel.rect.y + self.content_panel.rect.height - 10:
                break
                
            self.building_panels[building_id] = BuildingPanel(
                pygame.Rect(x_pos, y_pos, column_width - 10, panel_height),
                building_id,
                self.game_state
            )
    
    def create_research_panels(self):
        # Clear existing research panels
        self.research_panels = {}
        
        # Get unlocked research
        unlocked_research = [research_id for research_id, research_data in self.game_state.research.items() 
                            if research_data["unlocked"]]
        
        if not unlocked_research:
            return
            
        # Calculate panel dimensions
        panel_height = 120
        panel_width = self.content_panel.rect.width - 40
        columns = 2
        column_width = panel_width // columns
        
        for i, research_id in enumerate(unlocked_research):
            column = i % columns
            row = i // columns
            
            x_pos = self.content_panel.rect.x + 20 + column * column_width
            y_pos = self.content_panel.rect.y + 20 + (panel_height + 10) * row
            
            # Skip if it would go off screen
            if y_pos + panel_height > self.content_panel.rect.y + self.content_panel.rect.height - 10:
                break
                
            self.research_panels[research_id] = ResearchPanel(
                pygame.Rect(x_pos, y_pos, column_width - 10, panel_height),
                research_id,
                self.game_state
            )
    
    def create_prestige_panels(self):
        # Clear existing prestige upgrade panels
        self.prestige_upgrade_panels = {}
        
        # Get all prestige upgrades
        prestige_upgrades = list(self.game_state.prestige_upgrades.keys())
        
        if not prestige_upgrades:
            return
            
        # Calculate panel dimensions
        panel_height = 100
        panel_width = self.content_panel.rect.width - 40
        columns = 2
        column_width = panel_width // columns
        
        # Start below the prestige information text
        start_y = self.content_panel.rect.y + 80
        
        for i, upgrade_id in enumerate(prestige_upgrades):
            column = i % columns
            row = i // columns
            
            x_pos = self.content_panel.rect.x + 20 + column * column_width
            y_pos = start_y + (panel_height + 10) * row
            
            # Skip if it would go off screen
            if y_pos + panel_height > self.content_panel.rect.y + self.content_panel.rect.height - 10:
                break
                
            self.prestige_upgrade_panels[upgrade_id] = PrestigePanel(
                pygame.Rect(x_pos, y_pos, column_width - 10, panel_height),
                upgrade_id,
                self.game_state
            )
    
    def create_achievement_panels(self):
        # Clear existing achievement panels
        self.achievement_panels = {}
        
        # Get all achievements
        achievements = list(self.game_state.achievements.keys())
        
        if not achievements:
            return
            
        # Calculate panel dimensions
        panel_height = 80
        panel_width = self.content_panel.rect.width - 40
        columns = 1  # Single column for achievements to show more details
        column_width = panel_width // columns
        
        # Start below the achievement information text
        start_y = self.content_panel.rect.y + 80
        
        for i, achievement_id in enumerate(achievements):
            column = i % columns
            row = i // columns
            
            x_pos = self.content_panel.rect.x + 20 + column * column_width
            y_pos = start_y + (panel_height + 10) * row
            
            # Skip if it would go off screen
            if y_pos + panel_height > self.content_panel.rect.y + self.content_panel.rect.height - 10:
                break
                
            self.achievement_panels[achievement_id] = AchievementPanel(
                pygame.Rect(x_pos, y_pos, column_width - 10, panel_height),
                achievement_id,
                self.game_state
            )
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            # Update bulk purchase panel
            self.bulk_purchase_panel.update(self.mouse_pos)
        
        if event.type == pygame.KEYDOWN:
            # Handle key presses for dialogs
            if self.show_save_dialog or self.show_load_dialog:
                self._handle_text_input(event)
            elif self.show_import_dialog:
                self._handle_text_input(event, multiline=True)
            elif self.show_export_dialog and event.key == pygame.K_ESCAPE:
                self.show_export_dialog = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Handle dialogs first if they're open
            if self.show_save_dialog:
                self._handle_save_dialog_click()
                return
            elif self.show_load_dialog:
                self._handle_load_dialog_click()
                return
            elif self.show_export_dialog:
                self._handle_export_dialog_click()
                return
            elif self.show_import_dialog:
                self._handle_import_dialog_click()
                return
            elif self.show_notification_detail:
                if handle_notification_detail_click(self, self.mouse_pos, self.close_button_rect):
                    return
                
            # Check for notification panel clicks
            clicked_notification_id = self.notification_panel.get_clicked_notification(self.mouse_pos)
            if clicked_notification_id is not None:
                self.current_notification = self.notification_panel.get_notification_by_id(clicked_notification_id)
                if self.current_notification:
                    self.show_notification_detail = True
                    return
            
            # Handle tab button clicks
            for tab, button in self.tab_buttons.items():
                if button.is_clicked(self.mouse_pos):
                    self.active_tab = tab
            
            # Handle save/load buttons
            if self.save_button.is_clicked(self.mouse_pos):
                self.show_save_dialog = True
                self.dialog_input_text = "save.json"
                self.dialog_cursor_pos = len(self.dialog_input_text)
            
            if self.load_button.is_clicked(self.mouse_pos):
                self.show_load_dialog = True
                self.dialog_input_text = "save.json"
                self.dialog_cursor_pos = len(self.dialog_input_text)
                
            # Handle export/import buttons
            if self.export_button.is_clicked(self.mouse_pos):
                save_string = self.game_state.export_save_string()
                if save_string:
                    self.show_export_dialog = True
                    self.dialog_input_text = save_string
                    self.dialog_cursor_pos = 0  # Start at beginning for easier selection
                    self.game_state.add_notification("Save exported! Copy the text below.")
                else:
                    self.game_state.add_notification("Failed to export save!")
            
            if self.import_button.is_clicked(self.mouse_pos):
                self.show_import_dialog = True
                self.dialog_input_text = ""
                self.dialog_cursor_pos = 0
            
            # Handle prestige button
            if self.prestige_button.is_clicked(self.mouse_pos):
                points = self.game_state.calculate_prestige_points()
                if points > 0:
                    if self.game_state.perform_prestige():
                        # Refresh UI components after prestige
                        self.create_race_panels()
                        self.create_building_panels()
                        self.create_research_panels()
                        self.create_prestige_panels()
                else:
                    self.game_state.add_notification("Not enough progress to prestige yet!")
            
            # Handle time warp button
            if self.time_warp_button.is_clicked(self.mouse_pos):
                self.game_state.activate_time_warp()
            
            # Handle bulk purchase button clicks
            if self.bulk_purchase_panel.x1_button.rect.collidepoint(event.pos):
                self.bulk_purchase_panel.select_button(self.bulk_purchase_panel.x1_button)
            elif self.bulk_purchase_panel.x10_button.rect.collidepoint(event.pos):
                self.bulk_purchase_panel.select_button(self.bulk_purchase_panel.x10_button)
            elif self.bulk_purchase_panel.x100_button.rect.collidepoint(event.pos):
                self.bulk_purchase_panel.select_button(self.bulk_purchase_panel.x100_button)
            elif self.bulk_purchase_panel.max_button.rect.collidepoint(event.pos):
                self.bulk_purchase_panel.select_button(self.bulk_purchase_panel.max_button)
            
            # Handle tab-specific interactions
            if self.active_tab == "races":
                # Handle race panel buttons
                for race_id, panel in self.race_panels.items():
                    if panel.buy_button.is_clicked(self.mouse_pos):
                        cost = self.game_state.get_race_purchase_cost(race_id)
                        if self.game_state.spend_resources(cost):
                            self.game_state.add_race(race_id)
                    
                    if panel.upgrade_button.is_clicked(self.mouse_pos):
                        cost = self.game_state.get_race_upgrade_cost(race_id)
                        if self.game_state.spend_resources(cost):
                            self.game_state.upgrade_race(race_id)
            
            elif self.active_tab == "buildings":
                # Handle building panel buttons
                for building_id, panel in self.building_panels.items():
                    if panel.buy_button.is_clicked(self.mouse_pos):
                        cost = self.game_state.get_building_purchase_cost(building_id)
                        if self.game_state.spend_resources(cost):
                            self.game_state.add_building(building_id)
                    
                    if panel.upgrade_button.is_clicked(self.mouse_pos):
                        cost = self.game_state.get_building_upgrade_cost(building_id)
                        if self.game_state.spend_resources(cost):
                            self.game_state.upgrade_building(building_id)
            
            elif self.active_tab == "research":
                # Handle research panel buttons
                for research_id, panel in self.research_panels.items():
                    if panel.research_button.is_clicked(self.mouse_pos):
                        cost = self.game_state.get_research_cost(research_id)
                        if self.game_state.spend_resources(cost):
                            self.game_state.research_technology(research_id)
            
            elif self.active_tab == "prestige":
                # Handle prestige upgrade panel buttons
                for upgrade_id, panel in self.prestige_upgrade_panels.items():
                    if panel.buy_button.is_clicked(self.mouse_pos):
                        cost = self.game_state.get_prestige_upgrade_cost(upgrade_id)
                        if self.game_state.spend_resources(cost):
                            self.game_state.purchase_prestige_upgrade(upgrade_id)
    
    def update(self):
        # Check for autosave
        current_time = pygame.time.get_ticks()
        if current_time - self.last_autosave_time > self.autosave_interval:
            if self.game_state.save_game("autosave.json", compress=True):
                self.game_state.add_notification("Game autosaved!")
            self.last_autosave_time = current_time
        
        # Update tab buttons
        for button in self.tab_buttons.values():
            button.update(self.mouse_pos)
        
        # Update save/load buttons
        self.save_button.update(self.mouse_pos)
        self.load_button.update(self.mouse_pos)
        self.export_button.update(self.mouse_pos)
        self.import_button.update(self.mouse_pos)
        self.prestige_button.update(self.mouse_pos)
        self.time_warp_button.update(self.mouse_pos)
        
        # Update notification panel
        self.notification_panel.update(self.mouse_pos)
        
        # Update tab-specific components
        if self.active_tab == "races":
            # Update race panels if new races are unlocked
            unlocked_count = sum(1 for race_data in self.game_state.races.values() if race_data["unlocked"])
            if unlocked_count != len(self.race_panels):
                self.create_race_panels()
                
            # Update all race panels with current mouse position and multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.race_panels.values():
                panel.update(self.mouse_pos, current_multiplier)
        
        elif self.active_tab == "buildings":
            # Update building panels if new buildings are unlocked
            unlocked_count = sum(1 for building_data in self.game_state.buildings.values() if building_data["unlocked"])
            if unlocked_count != len(self.building_panels):
                self.create_building_panels()
                
            # Update all building panels with current mouse position and multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.building_panels.values():
                panel.update(self.mouse_pos, current_multiplier)
        
        elif self.active_tab == "research":
            # Update research panels if new research is unlocked
            unlocked_count = sum(1 for research_data in self.game_state.research.values() if research_data["unlocked"])
            if unlocked_count != len(self.research_panels):
                self.create_research_panels()
                
            # Update all research panels with current mouse position and multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.research_panels.values():
                panel.update(self.mouse_pos, current_multiplier)
        
        elif self.active_tab == "prestige":
            # Update all prestige upgrade panels with current mouse position and multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.prestige_upgrade_panels.values():
                panel.update(self.mouse_pos, current_multiplier)
    
    def render(self):
        # Render resource panel and displays
        self.resource_panel.render(self.screen)
        for display in self.resource_displays.values():
            display.render(self.screen)
        
        # Render tab buttons
        for tab, button in self.tab_buttons.items():
            # Highlight active tab
            if tab == self.active_tab:
                original_color = button.color
                button.color = (button.color[0] + 30, button.color[1] + 30, button.color[2] + 30)
                button.render(self.screen)
                button.color = original_color
            else:
                button.render(self.screen)
        
        # Render content panel
        self.content_panel.render(self.screen)
        
        # Render tab-specific content
        if self.active_tab == "races":
            # Render race panels with current multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.race_panels.values():
                panel.render(self.screen, current_multiplier)
        
        elif self.active_tab == "buildings":
            # Render building panels with current multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.building_panels.values():
                panel.render(self.screen, current_multiplier)
        
        elif self.active_tab == "research":
            # Render research panels with current multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.research_panels.values():
                panel.render(self.screen, current_multiplier)
        
        elif self.active_tab == "prestige":
            # Render prestige information
            prestige_points_text = self.title_font.render(f"Prestige Points: {self.game_state.prestige_points}", True, PURPLE_COLOR)
            self.screen.blit(prestige_points_text, (self.content_panel.rect.x + 20, self.content_panel.rect.y + 20))
            
            potential_points_text = self.font.render(
                f"Potential points from prestige: {self.game_state.calculate_prestige_points()}", 
                True, TEXT_COLOR
            )
            self.screen.blit(potential_points_text, (self.content_panel.rect.x + 20, self.content_panel.rect.y + 50))
            
            # Render prestige upgrade panels with current multiplier
            current_multiplier = self.bulk_purchase_panel.get_multiplier()
            for panel in self.prestige_upgrade_panels.values():
                panel.render(self.screen, current_multiplier)
        
        elif self.active_tab == "achievements":
            # Render achievement information
            achievement_title = self.title_font.render("Achievements", True, GOLD_COLOR)
            self.screen.blit(achievement_title, (self.content_panel.rect.x + 20, self.content_panel.rect.y + 20))
            
            # Count unlocked achievements
            total_achievements = 0
            unlocked_achievements = 0
            for category in self.game_state.achievements.values():
                total_achievements += len(category)
                unlocked_achievements += sum(1 for achieved in category.values() if achieved)
            
            progress_text = self.font.render(
                f"Progress: {unlocked_achievements}/{total_achievements} achievements unlocked", 
                True, TEXT_COLOR
            )
            self.screen.blit(progress_text, (self.content_panel.rect.x + 20, self.content_panel.rect.y + 50))
            
            # Only display unlocked achievements
            self._render_achievement_list()
        
        # Render notification panel
        self.notification_panel.render(self.screen)
        
        # Render save/load buttons
        self.save_button.render(self.screen)
        self.load_button.render(self.screen)
        self.export_button.render(self.screen)
        self.import_button.render(self.screen)
        self.prestige_button.render(self.screen)
        self.time_warp_button.render(self.screen)
        
        # Render dialogs if active
        if self.show_save_dialog:
            self._render_save_dialog()
        elif self.show_load_dialog:
            self._render_load_dialog()
        elif self.show_export_dialog:
            self._render_export_dialog()
        elif self.show_import_dialog:
            self._render_import_dialog()
        elif self.show_notification_detail:
            self.close_button_rect = render_notification_detail(self, self.screen)
        
        # Render player level and prestige level
        level_text = self.font.render(f"Level: {self.game_state.player_level}", True, TEXT_COLOR)
        self.screen.blit(level_text, (20, 70))
        
        # Render bulk purchase panel
        self.bulk_purchase_panel.render(self.screen)
        
        # Render all collected tooltips in the foreground
        if self.active_tab == "races":
            for panel in self.race_panels.values():
                if panel.tooltip_data:
                    panel.render_tooltip(self.screen)
    
    def _render_achievement_list(self):
        """Render a list of unlocked achievements with their descriptions"""
        # Define display area
        list_area_x = self.content_panel.rect.x + 20
        list_area_y = self.content_panel.rect.y + 80
        list_area_width = self.content_panel.rect.width - 40
        list_area_height = self.content_panel.rect.height - 100
        
        # Achievement section titles and their corresponding categories in game_state.achievements
        achievement_sections = [
            ("Resource Achievements", "resource_milestones"),
            ("Race Achievements", "race_milestones"),
            ("Building Achievements", "building_milestones"),
            ("Prestige Achievements", "prestige_milestones"),
            ("Time Achievements", "time_milestones")
        ]
        
        # Import achievement data
        from game.constants import ACHIEVEMENTS
        
        # Track Y position for rendering
        current_y = list_area_y
        section_spacing = 30
        achievement_spacing = 50
        
        # Render each achievement section
        for section_title, category_key in achievement_sections:
            # Check if any achievements are unlocked in this category
            unlocked_in_category = False
            for achievement_id, is_unlocked in self.game_state.achievements[category_key].items():
                if is_unlocked:
                    unlocked_in_category = True
                    break
            
            # Skip section if no achievements unlocked
            if not unlocked_in_category:
                continue
                
            # Render section title
            section_title_text = self.title_font.render(section_title, True, GOLD_COLOR)
            self.screen.blit(section_title_text, (list_area_x, current_y))
            current_y += 25
            
            # Find the achievements in the constants file for this category
            achievements_in_category = ACHIEVEMENTS[category_key]
            
            # Render each unlocked achievement
            for achievement_data in achievements_in_category:
                achievement_id = achievement_data["id"]
                
                # Skip if not unlocked
                if not self.game_state.achievements[category_key][achievement_id]:
                    continue
                
                # Draw achievement background
                achievement_rect = pygame.Rect(list_area_x, current_y, list_area_width, achievement_spacing - 5)
                pygame.draw.rect(self.screen, (50, 120, 50, 180), achievement_rect)  # Green for unlocked
                pygame.draw.rect(self.screen, (100, 100, 120), achievement_rect, 1)  # Border
                
                # Achievement name
                name_text = self.font.render(achievement_data["name"], True, TEXT_COLOR)
                self.screen.blit(name_text, (list_area_x + 10, current_y + 5))
                
                # Achievement description
                desc_text = self.font.render(achievement_data["description"], True, TEXT_COLOR)
                self.screen.blit(desc_text, (list_area_x + 10, current_y + 25))
                
                # Move down for next achievement
                current_y += achievement_spacing
                
                # Check if we've reached the bottom of the display area
                if current_y >= list_area_y + list_area_height:
                    # Add a "More achievements not shown" message
                    more_text = self.font.render("More achievements not displayed due to space constraints...", True, TEXT_COLOR)
                    self.screen.blit(more_text, (list_area_x + 10, current_y - achievement_spacing + 5))
                    return
            
            # Add spacing between sections
            current_y += section_spacing
        
        prestige_text = self.font.render(f"Prestige: {self.game_state.prestige_count}", True, PURPLE_COLOR)
        self.screen.blit(prestige_text, (120, 70))
    
    def _handle_text_input(self, event, multiline=False):
        """Handle text input for dialogs"""
        if event.key == pygame.K_BACKSPACE:
            if self.dialog_cursor_pos > 0:
                self.dialog_input_text = (self.dialog_input_text[:self.dialog_cursor_pos-1] + 
                                          self.dialog_input_text[self.dialog_cursor_pos:])
                self.dialog_cursor_pos -= 1
        elif event.key == pygame.K_DELETE:
            if self.dialog_cursor_pos < len(self.dialog_input_text):
                self.dialog_input_text = (self.dialog_input_text[:self.dialog_cursor_pos] + 
                                          self.dialog_input_text[self.dialog_cursor_pos+1:])
        elif event.key == pygame.K_LEFT:
            if self.dialog_cursor_pos > 0:
                self.dialog_cursor_pos -= 1
        elif event.key == pygame.K_RIGHT:
            if self.dialog_cursor_pos < len(self.dialog_input_text):
                self.dialog_cursor_pos += 1
        elif event.key == pygame.K_HOME:
            self.dialog_cursor_pos = 0
        elif event.key == pygame.K_END:
            self.dialog_cursor_pos = len(self.dialog_input_text)
        elif event.key == pygame.K_RETURN:
            if not multiline:
                # For single line inputs, submit on enter
                if self.show_save_dialog:
                    self._save_game_from_dialog()
                elif self.show_load_dialog:
                    self._load_game_from_dialog()
        elif event.key == pygame.K_ESCAPE:
            # Close dialog on escape
            self.show_save_dialog = False
            self.show_load_dialog = False
            self.show_export_dialog = False
            self.show_import_dialog = False
        elif event.unicode and event.unicode.isprintable():
            # Add character at cursor position
            self.dialog_input_text = (self.dialog_input_text[:self.dialog_cursor_pos] + 
                                      event.unicode + 
                                      self.dialog_input_text[self.dialog_cursor_pos:])
            self.dialog_cursor_pos += 1
    
    def _handle_save_dialog_click(self):
        """Handle clicks in the save dialog"""
        dialog_width = 500
        dialog_height = 250
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        # Check input box click
        input_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 30)
        if input_rect.collidepoint(self.mouse_pos):
            # Set cursor position based on click position
            input_text_width = self.font.size(self.dialog_input_text)[0]
            click_offset = self.mouse_pos[0] - (input_rect.x + 5)
            if click_offset > input_text_width:
                self.dialog_cursor_pos = len(self.dialog_input_text)
            else:
                # Find closest character position
                for i in range(len(self.dialog_input_text) + 1):
                    if self.font.size(self.dialog_input_text[:i])[0] >= click_offset:
                        self.dialog_cursor_pos = i
                        break
            return
        
        # Check compression checkbox
        checkbox_rect = pygame.Rect(dialog_x + 20, dialog_y + 130, 20, 20)
        if checkbox_rect.collidepoint(self.mouse_pos):
            self.use_compression = not getattr(self, 'use_compression', False)
            return
        
        # Check save button (in-game save)
        save_button_rect = pygame.Rect(dialog_x + 40, dialog_y + 160, 120, 30)
        if save_button_rect.collidepoint(self.mouse_pos):
            self._save_game_from_dialog()
            return
            
        # Check local save button
        local_save_button_rect = pygame.Rect(dialog_x + 190, dialog_y + 160, 120, 30)
        if local_save_button_rect.collidepoint(self.mouse_pos):
            self._save_game_to_local_file()
            return
        
        # Check cancel button
        cancel_button_rect = pygame.Rect(dialog_x + 340, dialog_y + 160, 120, 30)
        if cancel_button_rect.collidepoint(self.mouse_pos):
            self.show_save_dialog = False
            return
    
    def _save_game_to_local_file(self):
        """Save the game to a local file using the filename from the dialog"""
        filename = self.dialog_input_text.strip()
        if filename:
            # Add .sav extension if not present
            if not filename.endswith('.sav'):
                filename += '.sav'
            
            # Create saves directory if it doesn't exist
            import os
            saves_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'saves')
            os.makedirs(saves_dir, exist_ok=True)
            
            # Save game to local file
            save_path = os.path.join(saves_dir, filename)
            
            try:
                # Use existing save game functionality but specify the full path
                self.game_state.save_game(save_path, getattr(self, 'use_compression', False))
                
                # Add notification
                self.game_state.add_notification(f"Game saved to file: {save_path}")
                
                # Close dialog
                self.show_save_dialog = False
                self.dialog_input_text = ""
                self.dialog_cursor_pos = 0
            except Exception as e:
                # Add error notification
                self.game_state.add_notification(f"Error saving game: {str(e)}")
    
    def _handle_load_dialog_click(self):
        """Handle clicks in the load dialog"""
        dialog_width = 400
        dialog_height = 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        
        # Check input box click
        input_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 30)
        if input_rect.collidepoint(self.mouse_pos):
            # Set cursor position based on click position
            input_text_width = self.font.size(self.dialog_input_text)[0]
            click_offset = self.mouse_pos[0] - (input_rect.x + 5)
            if click_offset > input_text_width:
                self.dialog_cursor_pos = len(self.dialog_input_text)
            else:
                # Find closest character position
                for i in range(len(self.dialog_input_text) + 1):
                    if self.font.size(self.dialog_input_text[:i])[0] >= click_offset:
                        self.dialog_cursor_pos = i
                        break
            return
        
        # Check load button
        load_button_rect = pygame.Rect(dialog_x + 80, dialog_y + 140, 100, 30)
        if load_button_rect.collidepoint(self.mouse_pos):
            self._load_game_from_dialog()
            return
        
        # Check cancel button
        cancel_button_rect = pygame.Rect(dialog_x + 220, dialog_y + 140, 100, 30)
        if cancel_button_rect.collidepoint(self.mouse_pos):
            self.show_load_dialog = False
            return
    
    def _handle_export_dialog_click(self):
        """Handle clicks in the export dialog"""
        dialog_width = 600
        dialog_height = 300
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        
        # Check close button
        close_button_rect = pygame.Rect(dialog_x + (dialog_width - 100) // 2, dialog_y + 250, 100, 30)
        if close_button_rect.collidepoint(self.mouse_pos):
            self.show_export_dialog = False
            return
    
    def _handle_import_dialog_click(self):
        """Handle clicks in the import dialog"""
        dialog_width = 600
        dialog_height = 300
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        
        # Check text box click
        text_box_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 150)
        if text_box_rect.collidepoint(self.mouse_pos):
            # Set cursor position based on click position
            # This is simplified - for a real implementation, we'd need to handle wrapped text
            self.dialog_cursor_pos = min(len(self.dialog_input_text), 
                                        int((self.mouse_pos[0] - text_box_rect.x) / 10))
            return
        
        # Check import button
        import_button_rect = pygame.Rect(dialog_x + 150, dialog_y + 250, 100, 30)
        if import_button_rect.collidepoint(self.mouse_pos):
            self._import_save_from_dialog()
            return
        
        # Check cancel button
        cancel_button_rect = pygame.Rect(dialog_x + 350, dialog_y + 250, 100, 30)
        if cancel_button_rect.collidepoint(self.mouse_pos):
            self.show_import_dialog = False
            return
    
    def _save_game_from_dialog(self):
        """Save the game with the filename from the dialog"""
        filename = self.dialog_input_text.strip()
        if not filename:
            self.game_state.add_notification("Please enter a valid filename!")
            return
        
        # Add .json extension if not present
        if not filename.endswith(".json"):
            filename += ".json"
        
        # Get compression setting
        use_compression = getattr(self, 'use_compression', False)
        
        if self.game_state.save_game(filename, compress=use_compression):
            self.game_state.add_notification(f"Game saved to {filename}!")
            self.show_save_dialog = False
        else:
            self.game_state.add_notification("Failed to save game!")
    
    def _load_game_from_dialog(self):
        """Load the game with the filename from the dialog"""
        filename = self.dialog_input_text.strip()
        if not filename:
            self.game_state.add_notification("Please enter a valid filename!")
            return
        
        # Add .json extension if not present
        if not filename.endswith(".json"):
            filename += ".json"
        
        if self.game_state.load_game(filename):
            self.game_state.add_notification(f"Game loaded from {filename}!")
            self.show_load_dialog = False
            
            # Refresh UI components
            self.create_race_panels()
            self.create_building_panels()
            self.create_research_panels()
            self.create_prestige_panels()
        else:
            self.game_state.add_notification(f"Failed to load game from {filename}!")
    
    def _import_save_from_dialog(self):
        """Import the game from the save string in the dialog"""
        save_string = self.dialog_input_text.strip()
        if not save_string:
            self.game_state.add_notification("Please enter a valid save string!")
            return
        
        if self.game_state.import_save_string(save_string):
            self.game_state.add_notification("Game imported successfully!")
            self.show_import_dialog = False
            
            # Refresh UI components
            self.create_race_panels()
            self.create_building_panels()
            self.create_research_panels()
            self.create_prestige_panels()
        else:
            self.game_state.add_notification("Failed to import game! Invalid save string.")
    
    def _render_save_dialog(self):
        """Render the save game dialog"""
        # Draw dialog background
        dialog_width = 500
        dialog_height = 250
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(self.screen, PANEL_COLOR, dialog_rect)
        pygame.draw.rect(self.screen, (150, 150, 170), dialog_rect, 2)  # Border
        
        # Draw title
        title_text = self.title_font.render("Save Game", True, TEXT_COLOR)
        self.screen.blit(title_text, (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 20))
        
        # Draw instructions
        instructions = self.font.render("Enter filename to save:", True, TEXT_COLOR)
        self.screen.blit(instructions, (dialog_x + 20, dialog_y + 60))
        
        # Draw input box
        input_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect)  # White background
        pygame.draw.rect(self.screen, (100, 100, 120), input_rect, 1)  # Border
        
        # Draw filename extension hint
        extension_hint = self.font.render(".sav", True, (150, 150, 150))
        if not self.dialog_input_text.endswith(".sav"):
            self.screen.blit(extension_hint, (input_rect.x + 5 + self.font.size(self.dialog_input_text)[0], input_rect.y + 5))
        
        # Draw input text
        input_text_surface = self.font.render(self.dialog_input_text, True, (0, 0, 0))
        self.screen.blit(input_text_surface, (input_rect.x + 5, input_rect.y + 5))
        
        # Draw cursor
        if pygame.time.get_ticks() % 1000 < 500:  # Blink cursor
            cursor_text = self.dialog_input_text[:self.dialog_cursor_pos]
            cursor_width = self.font.size(cursor_text)[0]
            pygame.draw.line(self.screen, (0, 0, 0), 
                            (input_rect.x + 5 + cursor_width, input_rect.y + 5),
                            (input_rect.x + 5 + cursor_width, input_rect.y + 25), 2)
        
        # Draw compression checkbox
        checkbox_rect = pygame.Rect(dialog_x + 20, dialog_y + 130, 20, 20)
        pygame.draw.rect(self.screen, (255, 255, 255), checkbox_rect)  # White background
        pygame.draw.rect(self.screen, (100, 100, 120), checkbox_rect, 1)  # Border
        
        # Draw checkbox state
        if getattr(self, 'use_compression', False):
            pygame.draw.line(self.screen, (0, 0, 0), 
                            (checkbox_rect.x + 3, checkbox_rect.y + 10),
                            (checkbox_rect.x + 8, checkbox_rect.y + 15), 2)
            pygame.draw.line(self.screen, (0, 0, 0), 
                            (checkbox_rect.x + 8, checkbox_rect.y + 15),
                            (checkbox_rect.x + 17, checkbox_rect.y + 5), 2)
        
        # Draw checkbox label
        checkbox_label = self.font.render("Use compression", True, TEXT_COLOR)
        self.screen.blit(checkbox_label, (checkbox_rect.x + 30, checkbox_rect.y))
        
        # Draw buttons
        save_button_rect = pygame.Rect(dialog_x + 40, dialog_y + 160, 120, 30)
        local_save_button_rect = pygame.Rect(dialog_x + 190, dialog_y + 160, 120, 30)
        cancel_button_rect = pygame.Rect(dialog_x + 340, dialog_y + 160, 120, 30)
        
        # Highlight buttons on hover
        save_button_color = BUTTON_HOVER_COLOR if save_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        local_save_button_color = BUTTON_HOVER_COLOR if local_save_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        cancel_button_color = BUTTON_HOVER_COLOR if cancel_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        
        pygame.draw.rect(self.screen, save_button_color, save_button_rect)
        pygame.draw.rect(self.screen, local_save_button_color, local_save_button_rect)
        pygame.draw.rect(self.screen, cancel_button_color, cancel_button_rect)
        
        # Draw button borders
        pygame.draw.rect(self.screen, (150, 150, 170), save_button_rect, 1)
        pygame.draw.rect(self.screen, (150, 150, 170), local_save_button_rect, 1)
        pygame.draw.rect(self.screen, (150, 150, 170), cancel_button_rect, 1)
        
        # Draw button text
        save_text = self.font.render("Save", True, TEXT_COLOR)
        local_save_text = self.font.render("Save to File", True, TEXT_COLOR)
        cancel_text = self.font.render("Cancel", True, TEXT_COLOR)
        
        self.screen.blit(save_text, (save_button_rect.x + (save_button_rect.width - save_text.get_width()) // 2, 
                                    save_button_rect.y + (save_button_rect.height - save_text.get_height()) // 2))
        self.screen.blit(local_save_text, (local_save_button_rect.x + (local_save_button_rect.width - local_save_text.get_width()) // 2, 
                                    local_save_button_rect.y + (local_save_button_rect.height - local_save_text.get_height()) // 2))
        self.screen.blit(cancel_text, (cancel_button_rect.x + (cancel_button_rect.width - cancel_text.get_width()) // 2, 
                                    cancel_button_rect.y + (cancel_button_rect.height - cancel_text.get_height()) // 2))
        
        # Draw additional instructions for local save
        local_save_info = self.font.render("Local saves will be stored in the 'saves' directory", True, TEXT_COLOR)
        self.screen.blit(local_save_info, (dialog_x + (dialog_width - local_save_info.get_width()) // 2, dialog_y + 200))
    
    def _render_load_dialog(self):
        """Render the load game dialog"""
        # Draw dialog background
        dialog_width = 400
        dialog_height = 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(self.screen, PANEL_COLOR, dialog_rect)
        pygame.draw.rect(self.screen, (150, 150, 170), dialog_rect, 2)  # Border
        
        # Draw title
        title_text = self.title_font.render("Load Game", True, TEXT_COLOR)
        self.screen.blit(title_text, (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 20))
        
        # Draw instructions
        instructions = self.font.render("Enter filename to load:", True, TEXT_COLOR)
        self.screen.blit(instructions, (dialog_x + 20, dialog_y + 60))
        
        # Draw input box
        input_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect)  # White background
        pygame.draw.rect(self.screen, (100, 100, 120), input_rect, 1)  # Border
        
        # Draw input text
        input_text_surface = self.font.render(self.dialog_input_text, True, (0, 0, 0))
        self.screen.blit(input_text_surface, (input_rect.x + 5, input_rect.y + 5))
        
        # Draw cursor
        if pygame.time.get_ticks() % 1000 < 500:  # Blink cursor
            cursor_text = self.dialog_input_text[:self.dialog_cursor_pos]
            cursor_width = self.font.size(cursor_text)[0]
            pygame.draw.line(self.screen, (0, 0, 0), 
                            (input_rect.x + 5 + cursor_width, input_rect.y + 5),
                            (input_rect.x + 5 + cursor_width, input_rect.y + 25), 2)
        
        # Draw buttons
        load_button_rect = pygame.Rect(dialog_x + 80, dialog_y + 140, 100, 30)
        cancel_button_rect = pygame.Rect(dialog_x + 220, dialog_y + 140, 100, 30)
        
        # Highlight buttons on hover
        load_button_color = BUTTON_HOVER_COLOR if load_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        cancel_button_color = BUTTON_HOVER_COLOR if cancel_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        
        pygame.draw.rect(self.screen, load_button_color, load_button_rect)
        pygame.draw.rect(self.screen, cancel_button_color, cancel_button_rect)
        
        # Draw button borders
        pygame.draw.rect(self.screen, (150, 150, 170), load_button_rect, 1)
        pygame.draw.rect(self.screen, (150, 150, 170), cancel_button_rect, 1)
        
        # Draw button text
        load_text = self.font.render("Load", True, TEXT_COLOR)
        cancel_text = self.font.render("Cancel", True, TEXT_COLOR)
        
        self.screen.blit(load_text, (load_button_rect.x + (load_button_rect.width - load_text.get_width()) // 2, 
                                    load_button_rect.y + (load_button_rect.height - load_text.get_height()) // 2))
        self.screen.blit(cancel_text, (cancel_button_rect.x + (cancel_button_rect.width - cancel_text.get_width()) // 2, 
                                    cancel_button_rect.y + (cancel_button_rect.height - cancel_text.get_height()) // 2))
    
    def _render_export_dialog(self):
        """Render the export save dialog"""
        # Draw dialog background
        dialog_width = 600
        dialog_height = 300
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(self.screen, PANEL_COLOR, dialog_rect)
        pygame.draw.rect(self.screen, (150, 150, 170), dialog_rect, 2)  # Border
        
        # Draw title
        title_text = self.title_font.render("Export Save", True, TEXT_COLOR)
        self.screen.blit(title_text, (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 20))
        
        # Draw instructions
        instructions = self.font.render("Copy this alphanumeric code to save your game elsewhere:", True, TEXT_COLOR)
        self.screen.blit(instructions, (dialog_x + 20, dialog_y + 60))
        
        # Draw text box
        text_box_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 150)
        pygame.draw.rect(self.screen, (255, 255, 255), text_box_rect)  # White background
        pygame.draw.rect(self.screen, (100, 100, 120), text_box_rect, 1)  # Border
        
        # Draw save string (with wrapping)
        save_string = self.dialog_input_text
        # Limit to visible portion to avoid performance issues with very long strings
        visible_chars = 500  # Adjust based on font size and box dimensions
        if len(save_string) > visible_chars:
            save_string = save_string[:visible_chars] + "..."
        
        # Simple text wrapping
        max_width = text_box_rect.width - 10
        lines = []
        current_line = ""
        
        for char in save_string:
            test_line = current_line + char
            if self.font.size(test_line)[0] > max_width:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        # Draw wrapped text
        for i, line in enumerate(lines[:8]):  # Limit to 8 lines to fit in box
            text_surface = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (text_box_rect.x + 5, text_box_rect.y + 5 + i * 20))
        
        # Draw close button
        close_button_rect = pygame.Rect(dialog_x + (dialog_width - 100) // 2, dialog_y + 250, 100, 30)
        
        # Highlight button on hover
        close_button_color = BUTTON_HOVER_COLOR if close_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        
        pygame.draw.rect(self.screen, close_button_color, close_button_rect)
        pygame.draw.rect(self.screen, (150, 150, 170), close_button_rect, 1)  # Border
        
        # Draw button text
        close_text = self.font.render("Close", True, TEXT_COLOR)
        self.screen.blit(close_text, (close_button_rect.x + (close_button_rect.width - close_text.get_width()) // 2, 
                                     close_button_rect.y + (close_button_rect.height - close_text.get_height()) // 2))
    
    def _render_import_dialog(self):
        """Render the import save dialog"""
        # Draw dialog background
        dialog_width = 600
        dialog_height = 300
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        pygame.draw.rect(self.screen, PANEL_COLOR, dialog_rect)
        pygame.draw.rect(self.screen, (150, 150, 170), dialog_rect, 2)  # Border
        
        # Draw title
        title_text = self.title_font.render("Import Save", True, TEXT_COLOR)
        self.screen.blit(title_text, (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 20))
        
        # Draw instructions
        instructions = self.font.render("Paste your save string here:", True, TEXT_COLOR)
        self.screen.blit(instructions, (dialog_x + 20, dialog_y + 60))
        
        # Draw text box
        text_box_rect = pygame.Rect(dialog_x + 20, dialog_y + 90, dialog_width - 40, 150)
        pygame.draw.rect(self.screen, (255, 255, 255), text_box_rect)  # White background
        pygame.draw.rect(self.screen, (100, 100, 120), text_box_rect, 1)  # Border
        
        # Draw input text (with wrapping)
        input_text = self.dialog_input_text
        
        # Simple text wrapping
        max_width = text_box_rect.width - 10
        lines = []
        current_line = ""
        
        for char in input_text:
            test_line = current_line + char
            if self.font.size(test_line)[0] > max_width:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        # Draw wrapped text
        for i, line in enumerate(lines[:8]):  # Limit to 8 lines to fit in box
            text_surface = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (text_box_rect.x + 5, text_box_rect.y + 5 + i * 20))
        
        # Draw cursor
        if pygame.time.get_ticks() % 1000 < 500:  # Blink cursor
            # Find cursor position in wrapped text
            cursor_pos = self.dialog_cursor_pos
            cursor_line = 0
            cursor_x = 0
            
            for i, line in enumerate(lines):
                if cursor_pos <= len(line):
                    cursor_line = i
                    cursor_x = self.font.size(line[:cursor_pos])[0]
                    break
                cursor_pos -= len(line)
            
            if cursor_line < 8:  # Only draw if cursor is visible
                pygame.draw.line(self.screen, (0, 0, 0), 
                                (text_box_rect.x + 5 + cursor_x, text_box_rect.y + 5 + cursor_line * 20),
                                (text_box_rect.x + 5 + cursor_x, text_box_rect.y + 25 + cursor_line * 20), 2)
        
        # Draw buttons
        import_button_rect = pygame.Rect(dialog_x + 150, dialog_y + 250, 100, 30)
        cancel_button_rect = pygame.Rect(dialog_x + 350, dialog_y + 250, 100, 30)
        
        # Highlight buttons on hover
        import_button_color = BUTTON_HOVER_COLOR if import_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        cancel_button_color = BUTTON_HOVER_COLOR if cancel_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
        
        pygame.draw.rect(self.screen, import_button_color, import_button_rect)
        pygame.draw.rect(self.screen, cancel_button_color, cancel_button_rect)
        
        # Draw button borders
        pygame.draw.rect(self.screen, (150, 150, 170), import_button_rect, 1)
        pygame.draw.rect(self.screen, (150, 150, 170), cancel_button_rect, 1)
        
        # Draw button text
        import_text = self.font.render("Import", True, TEXT_COLOR)
        cancel_text = self.font.render("Cancel", True, TEXT_COLOR)
        
        self.screen.blit(import_text, (import_button_rect.x + (import_button_rect.width - import_text.get_width()) // 2, 
                                      import_button_rect.y + (import_button_rect.height - import_text.get_height()) // 2))
        self.screen.blit(cancel_text, (cancel_button_rect.x + (cancel_button_rect.width - cancel_text.get_width()) // 2, 
                                      cancel_button_rect.y + (cancel_button_rect.height - cancel_text.get_height()) // 2))
