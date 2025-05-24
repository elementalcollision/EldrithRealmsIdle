import pygame
from game.constants import (TEXT_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, PANEL_COLOR, GOLD_COLOR, RACES,
                           NOTIFICATION_COLOR_ACHIEVEMENT, NOTIFICATION_COLOR_UNLOCK, NOTIFICATION_COLOR_ERROR,
                           NOTIFICATION_COLOR_INFO, NOTIFICATION_COLOR_SAVE, DEFAULT_NOTIFICATION_COLOR,
                           NOTIFICATION_PREFIXES, DISABLED_BUTTON_COLOR, DISABLED_TEXT_COLOR,
                           DISABLED_BUTTON_BORDER_COLOR)

class Panel:
    def __init__(self, rect, color):
        self.rect = rect
        self.color = color
    
    def render(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 2)  # Border

class Button:
    def __init__(self, rect, text, callback=None):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER_COLOR
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 14)
        self.enabled = True  # Added enabled attribute
    
    def update(self, mouse_pos):
        if self.enabled:
            self.is_hovered = self.rect.collidepoint(mouse_pos)
        else:
            self.is_hovered = False # Ensure hover is off if disabled
    
    def render(self, surface):
        if not self.enabled:
            # Disabled state
            pygame.draw.rect(surface, DISABLED_BUTTON_COLOR, self.rect)
            pygame.draw.rect(surface, DISABLED_BUTTON_BORDER_COLOR, self.rect, 1) # Disabled border
            text_surface = self.font.render(self.text, True, DISABLED_TEXT_COLOR)
        else:
            # Enabled state (existing logic)
            color = self.hover_color if self.is_hovered else self.color
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, (150, 150, 170), self.rect, 1)  # Original border for enabled
            text_surface = self.font.render(self.text, True, TEXT_COLOR)

        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def is_clicked(self, mouse_pos):
        return self.enabled and self.rect.collidepoint(mouse_pos)

class ResourceDisplay:
    def __init__(self, rect, resource_type, game_state):
        self.rect = rect
        self.resource_type = resource_type
        self.game_state = game_state
        self.font = pygame.font.SysFont('Arial', 18)  # Increased font size
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)  # Increased font size
    
    def render(self, surface):
        # Format resource name with first letter capitalized
        resource_name = self.resource_type.capitalize()
        
        # Get current amount and generation rate
        amount = self.game_state.resources[self.resource_type]
        rate = self.game_state.calculate_resource_generation_rate(self.resource_type)
        
        # Determine text color based on resource type
        text_color = TEXT_COLOR
        if self.resource_type == "gold":
            text_color = GOLD_COLOR
        
        # Render resource name
        name_surface = self.title_font.render(resource_name, True, text_color)
        # Center the name text within the allocated width if possible, or position at start
        name_x = self.rect.x + (self.rect.width - name_surface.get_width()) // 2
        if name_x < self.rect.x: # Ensure it doesn't go off the left edge
            name_x = self.rect.x + 5 # Small padding
        surface.blit(name_surface, (name_x, self.rect.y + 5)) # Adjusted y for padding
        
        # Render amount
        amount_text = f"{amount:.1f}"
        amount_surface = self.font.render(amount_text, True, text_color)
        # Position amount below the name, centered
        amount_x = self.rect.x + (self.rect.width - amount_surface.get_width()) // 2
        if amount_x < self.rect.x:
            amount_x = self.rect.x + 5
        surface.blit(amount_surface, (amount_x, self.rect.y + 30)) # Adjusted y for new font size and spacing
        
        # Render rate
        rate_text = f"+{rate:.1f}/s"
        rate_surface = self.font.render(rate_text, True, text_color)
        # Position rate below amount, aligned to the right or centered if space is tight
        rate_x = self.rect.x + self.rect.width - rate_surface.get_width() - 5 # Small padding from right
        if rate_x < self.rect.x : # if it's too far left (e.g. very wide rate text)
            rate_x = self.rect.x + (self.rect.width - rate_surface.get_width()) // 2 # center it
        if rate_x < self.rect.x: # ensure it doesn't go off the left edge
            rate_x = self.rect.x + 5

        surface.blit(rate_surface, (rate_x, self.rect.y + 55)) # Adjusted y for new font size and spacing

class RacePanel:
    def __init__(self, rect, race_id, game_state):
        self.rect = rect
        self.race_id = race_id
        self.game_state = game_state
        self.race_info = RACES[race_id]
        self.race_data = game_state.races[race_id]
        
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Tooltip state
        self.show_upgrade_tooltip = False
        self.tooltip_rect = None
        self.tooltip_data = None  # Will store tooltip data to be rendered later
        
        # Create buttons
        button_width = 80
        button_height = 30
        
        self.buy_button = Button(
            pygame.Rect(rect.x + rect.width - button_width - 10, rect.y + 10, button_width, button_height),
            "Buy"
        )
        
        self.upgrade_button = Button(
            pygame.Rect(rect.x + rect.width - button_width - 10, rect.y + rect.height - button_height - 10, button_width, button_height),
            "Upgrade"
        )
        
        # Voxel graphic display area - position to the left of the buttons with 10px padding
        self.graphic_rect = pygame.Rect(rect.x + rect.width - button_width - 10 - 64 - 10, 
                                      rect.y + (rect.height - 64) // 2, 
                                      64, 64)
        
        # Race graphic reference (will be set by UI manager)
        self.race_graphic = None
    
    def update(self, mouse_pos, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1  # Use 1 for 'Max' for affordability checkayer can afford to buy this race with the current multiplier
        purchase_cost = self.game_state.get_race_purchase_cost(self.race_id, count)
        can_afford = self.game_state.can_afford(purchase_cost)
        
        # Update button states based on affordability
        self.buy_button.enabled = can_afford
        self.buy_button.update(mouse_pos)
        
        # For upgrade button, check if race is owned and can be upgraded
        has_race = self.race_data['count'] > 0
        race_max_level = self.race_info.get('max_level', float('inf')) # Get max_level, default to infinity if not defined
        at_max_level_for_race = self.race_data['level'] >= race_max_level

        if has_race and not at_max_level_for_race:
            upgrade_cost = self.game_state.get_race_upgrade_cost(self.race_id, count)
            can_afford_upgrade = self.game_state.can_afford(upgrade_cost)
            self.upgrade_button.enabled = can_afford_upgrade
        else:
            self.upgrade_button.enabled = False # Disabled if no race, or at max level
        self.upgrade_button.update(mouse_pos)
        
        # Check if mouse is hovering over upgrade button for tooltip (only if button could be enabled)
        self.show_upgrade_tooltip = has_race and not at_max_level_for_race and self.upgrade_button.rect.collidepoint(mouse_pos)
        
        # Update race data
        self.race_data = self.game_state.races[self.race_id]
    
    def handle_click(self, mouse_pos):
        """Handle click events on the race panel"""
        if self.buy_button.rect.collidepoint(mouse_pos) and self.buy_button.enabled:
            # Get bulk purchase multiplier
            # multiplier is already provided as a parameteretermine how many to buy
            if multiplier == -1:  # Max
                # Calculate maximum number of races that can be bought
                purchase_cost = self.game_state.get_race_purchase_cost(self.race_id)
                max_affordable = self.game_state.calculate_max_affordable(purchase_cost)
                count = max_affordable
            else:
                count = multiplier
            
            # Try to buy the races
            success = self.game_state.add_race(self.race_id, count)
            if success:
                self.game_state.add_notification(f"Bought {count} {self.race_info['name']}")
        
        if self.upgrade_button.rect.collidepoint(mouse_pos) and self.upgrade_button.enabled:
            # Get bulk purchase multiplier
            # multiplier is already provided as a parameteretermine how many times to upgrade
            if multiplier == -1:  # Max
                # Calculate maximum number of upgrades that can be done
                upgrade_cost = self.game_state.get_race_upgrade_cost(self.race_id)
                max_affordable = self.game_state.calculate_max_affordable(upgrade_cost)
                count = max_affordable
            else:
                count = multiplier
            
            # Try to upgrade the race
            for _ in range(count):
                success = self.game_state.upgrade_race(self.race_id)
                if not success:
                    break
            
            if success:
                self.game_state.add_notification(f"Upgraded {self.race_info['name']} {count} times")
    
    def render(self, surface, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1  # Use 1 for 'Max' for affordability check
        
        # Check if player can afford to buy this race with the current multiplier
        purchase_cost = self.game_state.get_race_purchase_cost(self.race_id, count)
        can_afford = self.game_state.can_afford(purchase_cost)
        
        # Draw panel background - gray out if can't afford
        if can_afford:
            # Normal panel color
            pygame.draw.rect(surface, PANEL_COLOR, self.rect)
            border_color = (100, 100, 120)
        else:
            # Grayed out panel color
            pygame.draw.rect(surface, (80, 80, 80), self.rect)  # Darker background
            border_color = (120, 120, 120)  # Gray border
        
        pygame.draw.rect(surface, border_color, self.rect, 1)  # Border
        
        # Determine text color based on affordability
        text_color = TEXT_COLOR if can_afford else (150, 150, 150)  # Normal or grayed out
        
        # Draw race name
        name_surface = self.title_font.render(self.race_info["name"], True, text_color)
        surface.blit(name_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw race count and level
        count_text = f"Count: {self.race_data['count']}"
        count_surface = self.font.render(count_text, True, text_color)
        surface.blit(count_surface, (self.rect.x + 10, self.rect.y + 35))
        
        level_text = f"Level: {self.race_data['level']}"
        level_surface = self.font.render(level_text, True, text_color)
        surface.blit(level_surface, (self.rect.x + 10, self.rect.y + 55))
        
        # Draw race description with word wrapping to ensure it's fully readable
        desc = self.race_info["description"]
        wrapped_desc = self._wrap_text(desc, self.rect.width - 20)
        
        # Calculate vertical position to center the description in the available space
        desc_y_start = self.rect.y + 75
        # Since the graphic is now on the side, we have more vertical space for the description
        available_height = self.rect.height - desc_y_start - 10  # 10px bottom padding
        total_desc_height = len(wrapped_desc) * 18  # Line height of 18 pixels
        
        # Center vertically in available space
        desc_y = desc_y_start + max(0, (available_height - total_desc_height) // 2)
        
        # Render each line of the description
        for line in wrapped_desc:
            desc_surface = self.font.render(line, True, text_color)  # Use the appropriate text color
            # Center horizontally
            desc_x = self.rect.x + (self.rect.width - desc_surface.get_width()) // 2
            surface.blit(desc_surface, (desc_x, desc_y))
            desc_y += 18  # Line spacing
        
        # Draw purchase cost with appropriate color based on current multiplier
        # multiplier is already provided as a parameter
        count = multiplier if multiplier != -1 else 1  # Use 1 for display, 'Max' is handled differently
        
        cost = self.game_state.get_race_purchase_cost(self.race_id, count)
        cost_text = f"Cost: {cost.get('gold', 0):.1f} gold"
        
        # Add multiplier indicator to cost text if not x1
        if multiplier > 1:
            cost_text = f"Cost (x{multiplier}): {cost.get('gold', 0):.1f} gold"
        elif multiplier == -1:  # Max
            max_affordable = self.game_state.calculate_max_affordable(self.game_state.get_race_purchase_cost(self.race_id, 1))
            if max_affordable > 0:
                max_cost = self.game_state.get_race_purchase_cost(self.race_id, max_affordable)
                cost_text = f"Cost (Max {max_affordable}): {max_cost.get('gold', 0):.1f} gold"
            else:
                cost_text = f"Cost (Max): {cost.get('gold', 0):.1f} gold"
        
        cost_color = GOLD_COLOR if can_afford else (150, 120, 50)  # Dimmed gold if can't afford
        cost_surface = self.font.render(cost_text, True, cost_color)
        surface.blit(cost_surface, (self.rect.x + 85, self.rect.y + 35))
        
        # Draw upgrade cost with appropriate color based on current multiplier
        # multiplier is already provided as a parameter
        count = multiplier if multiplier != -1 else 1  # Use 1 for display, 'Max' is handled differently
        
        upgrade_cost = self.game_state.get_race_upgrade_cost(self.race_id, count)
        upgrade_text = f"Upgrade: {upgrade_cost.get('gold', 0):.1f} gold"
        
        # Add multiplier indicator to upgrade text if not x1
        has_race = self.race_data['count'] > 0
        if has_race:
            if multiplier > 1:
                upgrade_text = f"Upgrade (x{multiplier}): {upgrade_cost.get('gold', 0):.1f} gold"
            elif multiplier == -1:  # Max
                max_affordable = self.game_state.calculate_max_affordable(self.game_state.get_race_upgrade_cost(self.race_id, 1))
                if max_affordable > 0:
                    max_cost = self.game_state.get_race_upgrade_cost(self.race_id, max_affordable)
                    upgrade_text = f"Upgrade (Max {max_affordable}): {max_cost.get('gold', 0):.1f} gold"
                else:
                    upgrade_text = f"Upgrade (Max): {upgrade_cost.get('gold', 0):.1f} gold"
        
        can_afford_upgrade = self.game_state.can_afford(upgrade_cost)
        upgrade_color = GOLD_COLOR if has_race and can_afford_upgrade else (150, 120, 50)
        upgrade_surface = self.font.render(upgrade_text, True, upgrade_color)
        surface.blit(upgrade_surface, (self.rect.x + 85, self.rect.y + 55))
        
        # Draw 8-bit voxel graphic for the race
        if self.race_graphic:
            # Draw the race graphic
            surface.blit(self.race_graphic, self.graphic_rect)
        else:
            # Draw a placeholder if no graphic is available
            graphic_color = (50, 50, 70) if can_afford else (40, 40, 50)  # Darker if can't afford
            pygame.draw.rect(surface, graphic_color, self.graphic_rect)
            placeholder_text = self.font.render(self.race_info["name"][0], True, text_color)
            text_rect = placeholder_text.get_rect(center=self.graphic_rect.center)
            surface.blit(placeholder_text, text_rect)
        
        # Draw buttons
        self.buy_button.render(surface)
        self.upgrade_button.render(surface)
        
        # Prepare tooltip data if hovering over upgrade button
        if self.show_upgrade_tooltip:
            self.tooltip_data = self._prepare_tooltip_data()
        else:
            self.tooltip_data = None
        
    def _prepare_tooltip_data(self):
        """Prepare tooltip data showing upgrade benefits"""
        tooltip_info = self.game_state.get_race_upgrade_benefits(self.race_id)

        if not tooltip_info:
            return None

        tooltip_lines = []

        # Upgrade Cost
        cost_text_parts = []
        if tooltip_info["upgrade_cost"]:
            for res, amount in tooltip_info["upgrade_cost"].items():
                cost_text_parts.append(f"{amount:.0f} {res.capitalize()}")
            cost_str = ", ".join(cost_text_parts) if cost_text_parts else "N/A"
        else:
            cost_str = "N/A"
        tooltip_lines.append(f"Upgrade Cost: {cost_str}")
        tooltip_lines.append("") # Spacer

        # Current Level Benefits
        tooltip_lines.append(f"Current Level ({tooltip_info['current_level']}):")
        if tooltip_info["current_benefits"]:
            for benefit, value in tooltip_info["current_benefits"].items():
                tooltip_lines.append(f"  - {benefit}: {value}")
        else:
            tooltip_lines.append("  - None")
        tooltip_lines.append("") # Spacer

        # Next Level Benefits
        tooltip_lines.append(f"Next Level ({tooltip_info['next_level']}):")
        if tooltip_info["next_level_benefits"]:
            for benefit, value in tooltip_info["next_level_benefits"].items():
                tooltip_lines.append(f"  - {benefit}: {value}")
        else:
            tooltip_lines.append("  - None (Max Level Reached or No Further Benefits)")
        
        # Calculate tooltip dimensions
        # Use a smaller font for tooltips to fit more information
        tooltip_font = pygame.font.SysFont('Arial', 12)
        line_height = 18  # Adjusted for smaller font
        padding = 8       # Adjusted for smaller font

        max_line_width = 0
        for line in tooltip_lines:
            line_width = tooltip_font.size(line)[0]
            max_line_width = max(max_line_width, line_width)
        
        tooltip_width = max_line_width + padding * 2
        tooltip_height = len(tooltip_lines) * line_height + padding * 2
        
        # Position tooltip above the upgrade button
        tooltip_x = self.upgrade_button.rect.centerx - tooltip_width // 2
        tooltip_y = self.upgrade_button.rect.y - tooltip_height - 5 # 5px spacing
        
        # Make sure tooltip stays within screen bounds (simple adjustment)
        # A more robust solution might involve checking against UIManager.screen_width/height
        if tooltip_x < 5: # Small padding from edge
            tooltip_x = 5
        if tooltip_y < 5:
            tooltip_y = self.upgrade_button.rect.bottom + 5
        if tooltip_x + tooltip_width > surface.get_width() - 5: # surface is passed in render_tooltip
             tooltip_x = surface.get_width() - tooltip_width - 5
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        return {
            "rect": tooltip_rect,
            "lines": tooltip_lines,
            "font": tooltip_font, # Pass the font to render_tooltip
            "line_height": line_height,
            "padding": padding
        }

    def render_tooltip(self, surface):
        """Render the tooltip if it's active"""
        if not self.tooltip_data:
            return

        tooltip_rect = self.tooltip_data["rect"]
        tooltip_lines = self.tooltip_data["lines"]
        tooltip_font = self.tooltip_data["font"] # Use the font from tooltip_data
        line_height = self.tooltip_data["line_height"]
        padding = self.tooltip_data["padding"]

        # Adjust position again just before rendering, in case screen size changed
        # This is a simplified check; ideally, UIManager would pass screen dimensions
        if tooltip_rect.right > surface.get_width() - 5:
            tooltip_rect.right = surface.get_width() - 5
        if tooltip_rect.left < 5:
            tooltip_rect.left = 5
        if tooltip_rect.bottom > surface.get_height() - 5:
            tooltip_rect.bottom = surface.get_height() -5
        if tooltip_rect.top < 5:
            tooltip_rect.top = 5

        # Draw tooltip background
        pygame.draw.rect(surface, (40, 40, 60), tooltip_rect) # Darker background
        pygame.draw.rect(surface, (120, 120, 150), tooltip_rect, 1)  # Softer Border

        # Draw tooltip text
        for i, line in enumerate(tooltip_lines):
            # Basic alternating color for section headers, can be improved
            is_header = "Cost:" in line or "Level" in line 
            text_color_to_use = GOLD_COLOR if is_header else TEXT_COLOR
            
            text_surface = tooltip_font.render(line, True, text_color_to_use)
            surface.blit(text_surface, (tooltip_rect.x + padding, tooltip_rect.y + padding + i * line_height))

    def _wrap_text(self, text, max_width):
        """Wrap text to fit within a given width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = self.font.size(word + ' ')[0]
            
            if current_width + word_width > max_width:
                # Line is full, start a new one
                if current_line:  # Make sure we don't add empty lines
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                # Add word to current line
                current_line.append(word)
                current_width += word_width
        
        # Add the last line if it's not empty
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines


class BuildingPanel:
    def __init__(self, rect, building_id, game_state):
        self.rect = rect
        self.building_id = building_id
        self.game_state = game_state
        from game.constants import BUILDINGS
        self.building_info = BUILDINGS[building_id]
        self.building_data = game_state.buildings[building_id]
        
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)

        # Tooltip state for upgrades
        self.show_upgrade_tooltip = False
        self.tooltip_data = None
        
        # Create buttons
        button_width = 80
        button_height = 30
        
        self.buy_button = Button(
            pygame.Rect(rect.x + rect.width - button_width - 10, rect.y + 10, button_width, button_height),
            "Buy"
        )
        
        self.upgrade_button = Button(
            pygame.Rect(rect.x + rect.width - button_width - 10, rect.y + rect.height - button_height - 10, button_width, button_height),
            "Upgrade"
        )
    
    def update(self, mouse_pos, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1  # Use 1 for 'Max' for affordability check
        
        # Check if player can afford to buy this building with the current multiplier
        purchase_cost = self.game_state.get_building_purchase_cost(self.building_id, count)
        can_afford = self.game_state.can_afford(purchase_cost)
        
        # Update button states based on affordability
        self.buy_button.enabled = can_afford
        self.buy_button.update(mouse_pos)
        
        # For upgrade button, check if building is owned and can be upgraded
        has_building = self.building_data['count'] > 0
        at_max_level = self.building_data['level'] >= self.building_info['max_level']
        
        if has_building and not at_max_level:
            upgrade_cost = self.game_state.get_building_upgrade_cost(self.building_id, count)
            can_afford_upgrade = self.game_state.can_afford(upgrade_cost)
            self.upgrade_button.enabled = can_afford_upgrade
        else:
            self.upgrade_button.enabled = False
        
        self.upgrade_button.update(mouse_pos)

        # Check if mouse is hovering over upgrade button for tooltip
        # Only show if the button is enabled (i.e., not max level and has building)
        self.show_upgrade_tooltip = self.upgrade_button.enabled and self.upgrade_button.rect.collidepoint(mouse_pos)
        
        # Update building data
        self.building_data = self.game_state.buildings[self.building_id]
    
    def render(self, surface, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1
        
        # Check if player can afford to buy this building with the current multiplier
        purchase_cost = self.game_state.get_building_purchase_cost(self.building_id, count)
        can_afford = self.game_state.can_afford(purchase_cost)
        
        # Determine background color based on affordability
        bg_color = PANEL_COLOR if can_afford else (60, 60, 70)  # Darker if can't afford
        text_color = TEXT_COLOR if can_afford else (180, 180, 200)  # Lighter if can't afford
        
        # Draw panel background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 1)  # Border
        
        # Draw building name with appropriate color
        name_surface = self.title_font.render(self.building_info["name"], True, text_color)
        surface.blit(name_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw building count and level with appropriate color
        count_text = f"Count: {self.building_data['count']}"
        count_surface = self.font.render(count_text, True, text_color)
        surface.blit(count_surface, (self.rect.x + 10, self.rect.y + 35))
        
        level_text = f"Level: {self.building_data['level']}/{self.building_info['max_level']}"
        level_surface = self.font.render(level_text, True, text_color)
        surface.blit(level_surface, (self.rect.x + 10, self.rect.y + 55))
        
        # Draw building production with appropriate color
        production_text = []
        if "resource_production" in self.building_info:
            for resource, amount in self.building_info["resource_production"].items():
                current_production = amount * self.building_data['level'] * self.game_state.get_production_multiplier(resource)
                production_text.append(f"{resource.capitalize()}: +{current_production:.1f}/s")
        # Handle buildings with global multipliers instead of direct resource production
        elif "global_multipliers" in self.building_info:
            for resource, multiplier in self.building_info["global_multipliers"].items():
                effect_multiplier = multiplier ** self.building_data['level']
                if resource == "all":
                    production_text.append(f"All resources: x{effect_multiplier:.2f}")
                else:
                    production_text.append(f"{resource.capitalize()}: x{effect_multiplier:.2f}")
        
        if production_text:
            production_str = ", ".join(production_text[:2])  # Show only first two resources to save space
            if len(production_text) > 2:
                production_str += "..."
            production_surface = self.font.render(f"Production: {production_str}", True, text_color)
            surface.blit(production_surface, (self.rect.x + 10, self.rect.y + 75))
        
        # Use the provided multiplier
        # multiplier is already provided as a parameter
        count = multiplier if multiplier != -1 else 1  # Use 1 for display, 'Max' is handled differently
        
        # Ensure count is an integer for the get_building_purchase_cost method
        # purchase_count = int(count) if count != -1 else count # Original logic
        
        display_count_for_cost = count
        cost_prefix = "Cost: "
        if multiplier > 1:
            cost_prefix = f"Cost (x{multiplier}): "
        elif multiplier == -1:  # Max
            max_buy_count = self.game_state.calculate_max_affordable(self.game_state.get_building_purchase_cost(self.building_id, 1))
            if max_buy_count > 0:
                display_count_for_cost = max_buy_count
                cost_prefix = f"Cost (Max {max_buy_count}): "
            else:
                display_count_for_cost = 1 # Show cost for 1 if cannot afford any for Max
                cost_prefix = f"Cost (Max 0): "
        
        # Draw purchase cost
        actual_cost_to_display = self.game_state.get_building_purchase_cost(self.building_id, display_count_for_cost if multiplier != -1 else (max_buy_count if max_buy_count > 0 else 1) )
        cost_text_parts = []
        for resource, amount in actual_cost_to_display.items():
            cost_text_parts.append(f"{resource.capitalize()}: {amount:.1f}")
        
        cost_text = cost_prefix + ", ".join(cost_text_parts[:2])  # Show only first two resources
        if len(cost_text_parts) > 2:
            cost_text += "..."
        
        cost_surface = self.font.render(cost_text, True, GOLD_COLOR)
        surface.blit(cost_surface, (self.rect.x + 120, self.rect.y + 35))
        
        # Draw buttons
        self.buy_button.render(surface)
        
        # Only show upgrade button if not at max level
        if self.building_data['level'] < self.building_info['max_level']:
            self.upgrade_button.render(surface)
            
            # Draw upgrade cost if not at max level
            # multiplier is already provided as a parameter
            
            display_count_for_upgrade = count
            upgrade_prefix = "Upgrade: "
            actual_upgrade_cost_to_display = {}

            if multiplier > 1:
                upgrade_prefix = f"Upgrade (x{multiplier}): "
            elif multiplier == -1:  # Max
                max_upgrade_count = self.game_state.calculate_max_affordable(self.game_state.get_building_upgrade_cost(self.building_id, 1))
                if max_upgrade_count > 0:
                    display_count_for_upgrade = max_upgrade_count
                    upgrade_prefix = f"Upgrade (Max {max_upgrade_count}): "
                else:
                    display_count_for_upgrade = 1 # Show cost for 1 if cannot afford any for Max
                    upgrade_prefix = f"Upgrade (Max 0): "
            
            actual_upgrade_cost_to_display = self.game_state.get_building_upgrade_cost(self.building_id, display_count_for_upgrade if multiplier != -1 else (max_upgrade_count if max_upgrade_count > 0 else 1))
            upgrade_text_parts = []
            for resource, amount in actual_upgrade_cost_to_display.items():
                upgrade_text_parts.append(f"{resource.capitalize()}: {amount:.1f}")
            
            upgrade_text = upgrade_prefix + ", ".join(upgrade_text_parts[:2])
            if len(upgrade_text_parts) > 2:
                upgrade_text += "..."
            
            # Check if player can afford the upgrade
            # For "Max", can_afford_upgrade should be true if max_upgrade_count > 0, or based on the actual_upgrade_cost_to_display
            can_afford_upgrade = self.game_state.can_afford(actual_upgrade_cost_to_display)
            if multiplier == -1 and max_upgrade_count == 0 : # If Max is 0, it's not affordable
                 can_afford_upgrade = False
                 
            upgrade_color = GOLD_COLOR if can_afford_upgrade else (150, 120, 50)
            
            upgrade_surface = self.font.render(upgrade_text, True, upgrade_color)
            surface.blit(upgrade_surface, (self.rect.x + 120, self.rect.y + 55))

        # Prepare tooltip data if hovering over upgrade button
        if self.show_upgrade_tooltip:
            self.tooltip_data = self._prepare_tooltip_data(surface) # Pass surface for width checking
        else:
            self.tooltip_data = None

    def _prepare_tooltip_data(self, surface): # Added surface parameter
        """Prepare tooltip data showing upgrade benefits for buildings"""
        tooltip_info = self.game_state.get_building_upgrade_benefits(self.building_id)

        if not tooltip_info:
            return None

        tooltip_lines = []

        # Upgrade Cost (only if not max level)
        if tooltip_info["current_level"] < tooltip_info["max_level"]:
            cost_text_parts = []
            if tooltip_info["upgrade_cost"]:
                for res, amount in tooltip_info["upgrade_cost"].items():
                    cost_text_parts.append(f"{amount:.0f} {res.capitalize()}")
                cost_str = ", ".join(cost_text_parts) if cost_text_parts else "N/A"
            else:
                cost_str = "N/A" # Should not happen if not max level
            tooltip_lines.append(f"Upgrade Cost: {cost_str}")
            tooltip_lines.append("")  # Spacer

        # Current Level Benefits
        tooltip_lines.append(f"Current Level ({tooltip_info['current_level']}):")
        if tooltip_info["current_benefits"]:
            for benefit, value in tooltip_info["current_benefits"].items():
                tooltip_lines.append(f"  - {benefit}: {value}")
        else:
            tooltip_lines.append("  - None")
        tooltip_lines.append("")  # Spacer

        # Next Level Benefits (only if not max level)
        if tooltip_info["current_level"] < tooltip_info["max_level"]:
            tooltip_lines.append(f"Next Level ({tooltip_info['next_level']}):")
            if tooltip_info["next_level_benefits"]:
                for benefit, value in tooltip_info["next_level_benefits"].items():
                    tooltip_lines.append(f"  - {benefit}: {value}")
            else:
                tooltip_lines.append("  - No further direct benefits.")
        else:
            tooltip_lines.append(f"Max Level ({tooltip_info['max_level']}) Reached")


        # Calculate tooltip dimensions (similar to RacePanel)
        tooltip_font = pygame.font.SysFont('Arial', 12)
        line_height = 18
        padding = 8

        max_line_width = 0
        for line in tooltip_lines:
            line_width = tooltip_font.size(line)[0]
            max_line_width = max(max_line_width, line_width)
        
        tooltip_width = max_line_width + padding * 2
        tooltip_height = len(tooltip_lines) * line_height + padding * 2
        
        tooltip_x = self.upgrade_button.rect.centerx - tooltip_width // 2
        tooltip_y = self.upgrade_button.rect.y - tooltip_height - 5 
        
        if tooltip_x < 5: tooltip_x = 5
        if tooltip_y < 5: tooltip_y = self.upgrade_button.rect.bottom + 5
        if surface and tooltip_x + tooltip_width > surface.get_width() - 5:
             tooltip_x = surface.get_width() - tooltip_width - 5
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        return {
            "rect": tooltip_rect,
            "lines": tooltip_lines,
            "font": tooltip_font,
            "line_height": line_height,
            "padding": padding
        }

    def render_tooltip(self, surface):
        """Render the tooltip if it's active (similar to RacePanel)"""
        if not self.tooltip_data:
            return

        tooltip_rect = self.tooltip_data["rect"]
        tooltip_lines = self.tooltip_data["lines"]
        tooltip_font = self.tooltip_data["font"]
        line_height = self.tooltip_data["line_height"]
        padding = self.tooltip_data["padding"]

        # Final position adjustment before drawing
        if tooltip_rect.right > surface.get_width() - 5:
            tooltip_rect.right = surface.get_width() - 5
        if tooltip_rect.left < 5:
            tooltip_rect.left = 5
        if tooltip_rect.bottom > surface.get_height() - 5: # Prevent going off bottom
            tooltip_rect.bottom = surface.get_height() - 5
        if tooltip_rect.top < 5: # Prevent going off top
            tooltip_rect.top = 5
            
        pygame.draw.rect(surface, (40, 40, 60), tooltip_rect) 
        pygame.draw.rect(surface, (120, 120, 150), tooltip_rect, 1)

        for i, line in enumerate(tooltip_lines):
            is_header = "Cost:" in line or "Level" in line or "Max Level" in line
            text_color_to_use = GOLD_COLOR if is_header else TEXT_COLOR
            text_surface = tooltip_font.render(line, True, text_color_to_use)
            surface.blit(text_surface, (tooltip_rect.x + padding, tooltip_rect.y + padding + i * line_height))


class ResearchPanel:
    def __init__(self, rect, research_id, game_state):
        self.rect = rect
        self.research_id = research_id
        self.game_state = game_state
        from game.constants import RESEARCH
        self.research_info = RESEARCH[research_id]
        self.research_data = game_state.research[research_id]
        
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)

        # Tooltip state for research button
        self.show_tooltip = False
        self.tooltip_data = None
        
        # Create research button
        button_width = 80
        button_height = 30
        
        self.research_button = Button(
            pygame.Rect(rect.x + rect.width - button_width - 10, rect.y + rect.height - button_height - 10, button_width, button_height),
            "Research"
        )
    
    def update(self, mouse_pos, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1  # Use 1 for 'Max' for affordability check
        
        # Check if player can afford to research with the current multiplier
        research_cost = self.game_state.get_research_cost(self.research_id, count)
        can_afford = self.game_state.can_afford(research_cost)
        at_max_level = self.research_data['level'] >= self.research_info['max_level']
        
        # Update button states based on affordability and max level
        self.research_button.enabled = can_afford and not at_max_level
        self.research_button.update(mouse_pos)

        # Check if mouse is hovering over research button for tooltip
        self.show_tooltip = self.research_button.enabled and self.research_button.rect.collidepoint(mouse_pos)
        
        # Update research data
        self.research_data = self.game_state.research[self.research_id]
    
    def render(self, surface, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1
        
        # Check if player can afford to research with the current multiplier
        research_cost = self.game_state.get_research_cost(self.research_id, count)
        can_afford = self.game_state.can_afford(research_cost)
        at_max_level = self.research_data['level'] >= self.research_info['max_level']
        
        # Determine background color based on affordability and max level
        bg_color = PANEL_COLOR
        text_color = TEXT_COLOR
        
        if at_max_level:
            # Max level reached - use a slightly greenish tint
            bg_color = (60, 70, 60)
            text_color = (180, 220, 180)
        elif not can_afford:
            # Can't afford - use darker colors
            bg_color = (60, 60, 70)
            text_color = (180, 180, 200)
        
        # Draw panel background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 1)  # Border
        
        # Draw research name with appropriate color
        name_surface = self.title_font.render(self.research_info["name"], True, text_color)
        surface.blit(name_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw research level with appropriate color
        level_text = f"Level: {self.research_data['level']}/{self.research_info['max_level']}"
        level_surface = self.font.render(level_text, True, text_color)
        surface.blit(level_surface, (self.rect.x + 10, self.rect.y + 35))
        
        # Draw research description with appropriate color (truncated if necessary)
        desc = self.research_info["description"]
        if len(desc) > 50:
            desc = desc[:47] + "..."
        desc_surface = self.font.render(desc, True, text_color)
        surface.blit(desc_surface, (self.rect.x + 10, self.rect.y + 55))
        
        # Draw research effects with appropriate color
        effect_text = []
        if "resource_multiplier" in self.research_info["effect"]:
            for resource, multiplier in self.research_info["effect"]["resource_multiplier"].items():
                current_effect = 1 + (multiplier - 1) * self.research_data['level']
                effect_text.append(f"{resource.capitalize()}: x{current_effect:.2f}")
        
        if effect_text:
            effect_str = ", ".join(effect_text[:2])  # Show only first two effects
            if len(effect_text) > 2:
                effect_str += "..."
            effect_surface = self.font.render(f"Effect: {effect_str}", True, text_color)
            surface.blit(effect_surface, (self.rect.x + 10, self.rect.y + 75))
        
        # Use the provided multiplier
        # multiplier is already provided as a parameter
        count = multiplier if multiplier != -1 else 1  # Use 1 for display, 'Max' is handled differently
        
        # Draw research cost with current multiplier
        cost = self.game_state.get_research_cost(self.research_id, count)
        cost_text_parts = []
        for resource, amount in cost.items():
            cost_text_parts.append(f"{resource.capitalize()}: {amount:.1f}")
        
        # Base cost text
        cost_prefix = "Cost: "
        
        # Add multiplier indicator to cost text if not x1
        actual_cost_to_display = cost # Default to cost for 'count' or 1
        if multiplier > 1:
            cost_prefix = f"Cost (x{multiplier}): "
        elif multiplier == -1:  # Max
            max_affordable_levels = self.game_state.calculate_max_affordable_levels(
                self.research_id, 
                'get_research_cost', 
                self.research_data['level'], 
                self.research_info['max_level']
            )
            if max_affordable_levels > 0:
                actual_cost_to_display = self.game_state.get_research_cost(self.research_id, count=max_affordable_levels)
                cost_prefix = f"Cost (Max {max_affordable_levels}): "
            else:
                # Show cost for 1 level if cannot afford any for Max
                actual_cost_to_display = self.game_state.get_research_cost(self.research_id, count=1) 
                cost_prefix = f"Cost (Max 0): "
        
        cost_text_parts = [] # Re-calculate parts based on actual_cost_to_display
        for resource, amount in actual_cost_to_display.items():
            cost_text_parts.append(f"{resource.capitalize()}: {amount:.1f}")
        cost_text = cost_prefix + ", ".join(cost_text_parts)
        
        # Check if player can afford the displayed cost
        can_afford = self.game_state.can_afford(actual_cost_to_display)
        
        cost_color = GOLD_COLOR if can_afford else (150, 120, 50)
        
        cost_surface = self.font.render(cost_text, True, cost_color)
        surface.blit(cost_surface, (self.rect.x + 10, self.rect.y + 95))
        
        # Draw research button (only if not at max level)
        if self.research_data['level'] < self.research_info['max_level']:
            self.research_button.render(surface)
        else:
            max_level_text = self.font.render("Maximum Level Reached", True, (0, 200, 0))
            surface.blit(max_level_text, (self.rect.x + 10, self.rect.y + self.rect.height - 25))
            
        # Prepare tooltip data if hovering over research button
        if self.show_tooltip:
            self.tooltip_data = self._prepare_tooltip_data(surface)
        else:
            self.tooltip_data = None

    def _prepare_tooltip_data(self, surface):
        """Prepare tooltip data showing research benefits"""
        tooltip_info = self.game_state.get_research_upgrade_benefits(self.research_id)

        if not tooltip_info:
            return None

        tooltip_lines = []

        # Research Cost (only if not max level)
        if tooltip_info["current_level"] < tooltip_info["max_level"]:
            cost_text_parts = []
            if tooltip_info["research_cost"]:
                for res, amount in tooltip_info["research_cost"].items():
                    cost_text_parts.append(f"{amount:.0f} {res.capitalize()}")
                cost_str = ", ".join(cost_text_parts) if cost_text_parts else "N/A"
            else: # Should not happen if not max level
                cost_str = "N/A" 
            tooltip_lines.append(f"Research Cost: {cost_str}")
            tooltip_lines.append("")  # Spacer

        # Current Level Effects
        tooltip_lines.append(f"Current Level ({tooltip_info['current_level']}):")
        if tooltip_info["current_effects"]:
            for effect, value in tooltip_info["current_effects"].items():
                tooltip_lines.append(f"  - {effect}: {value}")
        else:
            tooltip_lines.append("  - None or Inactive")
        tooltip_lines.append("")  # Spacer

        # Next Level Effects (only if not max level)
        if tooltip_info["current_level"] < tooltip_info["max_level"]:
            tooltip_lines.append(f"Next Level ({tooltip_info['next_level']}):")
            if tooltip_info["next_level_effects"]:
                for effect, value in tooltip_info["next_level_effects"].items():
                    tooltip_lines.append(f"  - {effect}: {value}")
            else:
                tooltip_lines.append("  - No further direct effects.")
        else:
            tooltip_lines.append(f"Max Level ({tooltip_info['max_level']}) Reached")

        # Calculate tooltip dimensions (similar to BuildingPanel)
        tooltip_font = pygame.font.SysFont('Arial', 12)
        line_height = 18
        padding = 8

        max_line_width = 0
        for line in tooltip_lines:
            line_width = tooltip_font.size(line)[0]
            max_line_width = max(max_line_width, line_width)
        
        tooltip_width = max_line_width + padding * 2
        tooltip_height = len(tooltip_lines) * line_height + padding * 2
        
        tooltip_x = self.research_button.rect.centerx - tooltip_width // 2
        tooltip_y = self.research_button.rect.y - tooltip_height - 5
        
        if tooltip_x < 5: tooltip_x = 5
        if tooltip_y < 5: tooltip_y = self.research_button.rect.bottom + 5
        if surface and tooltip_x + tooltip_width > surface.get_width() - 5:
             tooltip_x = surface.get_width() - tooltip_width - 5
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        return {
            "rect": tooltip_rect,
            "lines": tooltip_lines,
            "font": tooltip_font,
            "line_height": line_height,
            "padding": padding
        }

    def render_tooltip(self, surface):
        """Render the tooltip if it's active (similar to BuildingPanel)"""
        if not self.tooltip_data:
            return

        tooltip_rect = self.tooltip_data["rect"]
        tooltip_lines = self.tooltip_data["lines"]
        tooltip_font = self.tooltip_data["font"]
        line_height = self.tooltip_data["line_height"]
        padding = self.tooltip_data["padding"]

        if tooltip_rect.right > surface.get_width() - 5:
            tooltip_rect.right = surface.get_width() - 5
        if tooltip_rect.left < 5:
            tooltip_rect.left = 5
        if tooltip_rect.bottom > surface.get_height() - 5:
            tooltip_rect.bottom = surface.get_height() - 5
        if tooltip_rect.top < 5:
            tooltip_rect.top = 5
            
        pygame.draw.rect(surface, (40, 40, 60), tooltip_rect) 
        pygame.draw.rect(surface, (120, 120, 150), tooltip_rect, 1)

        for i, line in enumerate(tooltip_lines):
            is_header = "Cost:" in line or "Level" in line or "Max Level" in line
            text_color_to_use = GOLD_COLOR if is_header else TEXT_COLOR
            text_surface = tooltip_font.render(line, True, text_color_to_use)
            surface.blit(text_surface, (tooltip_rect.x + padding, tooltip_rect.y + padding + i * line_height))


class PrestigePanel:
    def __init__(self, rect, upgrade_id, game_state):
        self.rect = rect
        self.upgrade_id = upgrade_id
        self.game_state = game_state
        from game.constants import PRESTIGE_UPGRADES
        self.upgrade_info = PRESTIGE_UPGRADES[upgrade_id]
        self.upgrade_data = game_state.prestige_upgrades[upgrade_id]
        
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Create purchase button
        button_width = 80
        button_height = 30
        
        self.buy_button = Button(
            pygame.Rect(rect.x + rect.width - button_width - 10, rect.y + rect.height - button_height - 10, button_width, button_height),
            "Purchase"
        )
    
    def update(self, mouse_pos, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1  # Use 1 for 'Max' for affordability check
        
        # Check if player can afford to purchase with the current multiplier
        purchase_cost = self.game_state.get_prestige_upgrade_cost(self.upgrade_id, count)
        can_afford = self.game_state.can_afford(purchase_cost)
        at_max_level = self.upgrade_data['level'] >= self.upgrade_info['max_level']
        
        # Update button states based on affordability and max level
        self.buy_button.enabled = can_afford and not at_max_level
        self.buy_button.update(mouse_pos)
        
        # Update upgrade data
        self.upgrade_data = self.game_state.prestige_upgrades[self.upgrade_id]
    
    def render(self, surface, current_multiplier=1):
        # Use the provided multiplier
        multiplier = current_multiplier
        count = multiplier if multiplier != -1 else 1
        
        # Check if player can afford to purchase with the current multiplier
        purchase_cost = self.game_state.get_prestige_upgrade_cost(self.upgrade_id, count)
        can_afford = self.game_state.can_afford(purchase_cost)
        at_max_level = self.upgrade_data['level'] >= self.upgrade_info['max_level']
        
        # Determine background color based on affordability and max level
        bg_color = PANEL_COLOR
        text_color = TEXT_COLOR
        
        if at_max_level:
            # Max level reached - use a slightly greenish tint
            bg_color = (60, 70, 60)
            text_color = (180, 220, 180)
        elif not can_afford:
            # Can't afford - use darker colors
            bg_color = (60, 60, 70)
            text_color = (180, 180, 200)
        
        # Draw panel background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 1)  # Border
        
        # Draw upgrade name with appropriate color
        name_surface = self.title_font.render(self.upgrade_info["name"], True, text_color)
        surface.blit(name_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw upgrade level with appropriate color
        level_text = f"Level: {self.upgrade_data['level']}/{self.upgrade_info['max_level']}"
        level_surface = self.font.render(level_text, True, text_color)
        surface.blit(level_surface, (self.rect.x + 10, self.rect.y + 35))
        
        # Draw upgrade description with appropriate color (truncated if necessary)
        desc = self.upgrade_info["description"]
        if len(desc) > 50:
            desc = desc[:47] + "..."
        desc_surface = self.font.render(desc, True, text_color)
        surface.blit(desc_surface, (self.rect.x + 10, self.rect.y + 55))
        
        # Draw upgrade effect with appropriate color
        effect_text = ""
        if "knowledge_retention" in self.upgrade_info["effect"]:
            retention = self.upgrade_info["effect"]["knowledge_retention"] * self.upgrade_data["level"]
            effect_text = f"Retain {retention*100:.1f}% knowledge after prestige"
        
        if effect_text:
            effect_surface = self.font.render(effect_text, True, text_color)
            surface.blit(effect_surface, (self.rect.x + 10, self.rect.y + 75))
        
        # Use the provided multiplier
        # multiplier is already provided as a parameter
        count = multiplier if multiplier != -1 else 1  # Use 1 for display, 'Max' is handled differently
        
        # Draw upgrade cost with current multiplier
        cost = self.game_state.get_prestige_upgrade_cost(self.upgrade_id, count)
        
        # Base cost text
        cost_prefix = "Cost: "
        
        # Add multiplier indicator to cost text if not x1
        actual_cost_to_display = cost # Default to cost for 'count' or 1
        if multiplier > 1:
            cost_prefix = f"Cost (x{multiplier}): "
        elif multiplier == -1:  # Max
            max_affordable_levels = self.game_state.calculate_max_affordable_levels(
                self.upgrade_id,
                'get_prestige_upgrade_cost',
                self.upgrade_data['level'],
                self.upgrade_info['max_level']
            )
            if max_affordable_levels > 0:
                actual_cost_to_display = self.game_state.get_prestige_upgrade_cost(self.upgrade_id, count=max_affordable_levels)
                cost_prefix = f"Cost (Max {max_affordable_levels}): "
            else:
                # Show cost for 1 level if cannot afford any for Max
                actual_cost_to_display = self.game_state.get_prestige_upgrade_cost(self.upgrade_id, count=1)
                cost_prefix = f"Cost (Max 0): "
        
        cost_text = f"{cost_prefix}{actual_cost_to_display.get('prestige_points', 0)} prestige points"
        
        # Check if player can afford the displayed cost
        can_afford = self.game_state.can_afford(actual_cost_to_display)
        
        cost_color = GOLD_COLOR if can_afford else (150, 120, 50)
        
        cost_surface = self.font.render(cost_text, True, cost_color)
        surface.blit(cost_surface, (self.rect.x + 10, self.rect.y + self.rect.height - 25))
        
        # Draw purchase button (only if not at max level)
        if self.upgrade_data['level'] < self.upgrade_info['max_level']:
            self.buy_button.render(surface)


class AchievementPanel:
    def __init__(self, rect, achievement_id, game_state):
        self.rect = rect
        self.achievement_id = achievement_id
        self.game_state = game_state
        from game.constants import ACHIEVEMENTS
        self.achievement_info = ACHIEVEMENTS[achievement_id]
        self.achievement_data = game_state.achievements[achievement_id]
        
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
    
    def render(self, surface):
        # Draw panel background
        background_color = PANEL_COLOR
        if self.achievement_data["completed"]:
            background_color = (50, 120, 50)  # Green for completed achievements
            
        pygame.draw.rect(surface, background_color, self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 1)  # Border
        
        # Draw achievement name
        name_surface = self.title_font.render(self.achievement_info["name"], True, TEXT_COLOR)
        surface.blit(name_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw achievement description
        desc = self.achievement_info["description"]
        if len(desc) > 60:
            desc = desc[:57] + "..."
        desc_surface = self.font.render(desc, True, TEXT_COLOR)
        surface.blit(desc_surface, (self.rect.x + 10, self.rect.y + 35))
        
        # Draw achievement progress
        if "progress" in self.achievement_data and "target" in self.achievement_info:
            progress = self.achievement_data["progress"]
            target = self.achievement_info["target"]
            progress_text = f"Progress: {progress}/{target} ({progress/target*100:.1f}%)"
            progress_surface = self.font.render(progress_text, True, TEXT_COLOR)
            surface.blit(progress_surface, (self.rect.x + 10, self.rect.y + 55))
        
        # Draw completion status
        if self.achievement_data["completed"]:
            completed_text = "Completed!"
            completed_surface = self.font.render(completed_text, True, (255, 255, 100))
            surface.blit(completed_surface, (self.rect.x + self.rect.width - completed_surface.get_width() - 10, self.rect.y + 10))
            
            # Draw reward if any
            if "reward" in self.achievement_info:
                reward_text = f"Reward: {self.achievement_info['reward']}"
                reward_surface = self.font.render(reward_text, True, (255, 255, 100))
                surface.blit(reward_surface, (self.rect.x + 10, self.rect.y + 75))


class NotificationPanel:
    def __init__(self, rect, game_state):
        self.rect = rect
        self.game_state = game_state
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Maximum number of notifications to display
        self.max_notifications = 5
        
        # Notification fade time (in milliseconds)
        self.notification_lifetime = 5000  # 5 seconds
        
        # For tracking clicked and hovered notifications
        self.hovered_notification = None
        self.notification_rects = {}
        
    def update(self, mouse_pos=None):
        # Remove expired notifications
        current_time = pygame.time.get_ticks()
        self.game_state.notifications = [
            notif for notif in self.game_state.notifications 
            if current_time - notif["time"] < self.notification_lifetime
        ]
        
        # Update hovered state
        self.hovered_notification = None
        if mouse_pos and self.rect.collidepoint(mouse_pos):
            for notif_id, rect in self.notification_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.hovered_notification = notif_id
                    break
        
    def render(self, surface):
        # Draw panel background with semi-transparency
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(200)  # Alpha level (0-255)
        s.fill(PANEL_COLOR)
        surface.blit(s, (self.rect.x, self.rect.y))
        
        # Reset notification rects dictionary
        self.notification_rects = {}
        
        # Draw border
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 1)
        
        # Draw title
        title_surface = self.title_font.render("Notifications", True, TEXT_COLOR)
        surface.blit(title_surface, (self.rect.x + 10, self.rect.y + 5))
        
        # Draw notifications (most recent first, limited to max_notifications)
        notifications_to_show = self.game_state.notifications[-self.max_notifications:] if self.game_state.notifications else []
        
        for i, notification in enumerate(reversed(notifications_to_show)):
            # Calculate alpha based on time remaining
            current_time = pygame.time.get_ticks()
            time_elapsed = current_time - notification["time"]
            alpha = 255
            
            # Fade out in the last second
            if time_elapsed > self.notification_lifetime - 1000:
                alpha = 255 * (1 - (time_elapsed - (self.notification_lifetime - 1000)) / 1000)
            
            # Draw notification text with appropriate alpha
            raw_text = notification.get("text", "New notification")
            notification_type = notification.get("type", "info") # Default to 'info'
            
            # Get prefix and base color based on type
            prefix = NOTIFICATION_PREFIXES.get(notification_type, NOTIFICATION_PREFIXES["default"])
            base_text_color = DEFAULT_NOTIFICATION_COLOR # Default color
            if notification_type == "achievement":
                base_text_color = NOTIFICATION_COLOR_ACHIEVEMENT
            elif notification_type == "unlock":
                base_text_color = NOTIFICATION_COLOR_UNLOCK
            elif notification_type == "error":
                base_text_color = NOTIFICATION_COLOR_ERROR
            elif notification_type == "save":
                base_text_color = NOTIFICATION_COLOR_SAVE
            elif notification_type == "info": # Explicitly set info color
                base_text_color = NOTIFICATION_COLOR_INFO

            notification_text_with_prefix = prefix + raw_text
                
            # Determine final text color - highlight on hover overrides type color
            final_text_color = base_text_color
            if notification.get("id") == self.hovered_notification:
                final_text_color = GOLD_COLOR  # Gold color for hover state (already defined)
                
            notification_surface = self.font.render(notification_text_with_prefix, True, final_text_color)
            notification_surface.set_alpha(int(alpha))
            
            y_pos = self.rect.y + 30 + (i * 22)
            surface.blit(notification_surface, (self.rect.x + 10, y_pos))
            
            # Store the rectangle for this notification for click detection
            notif_rect = pygame.Rect(self.rect.x + 10, y_pos, self.rect.width - 20, 20)
            if "id" in notification:
                self.notification_rects[notification["id"]] = notif_rect
            
            # Draw cursor icon to indicate clickable
            if notification.get("id") == self.hovered_notification:
                cursor_icon = self.font.render("ℹ️", True, (255, 215, 0))
                surface.blit(cursor_icon, (self.rect.x + self.rect.width - 25, y_pos))
    
    def get_clicked_notification(self, mouse_pos):
        """Return the notification ID if one was clicked, None otherwise"""
        if not self.rect.collidepoint(mouse_pos):
            return None
            
        for notif_id, rect in self.notification_rects.items():
            if rect.collidepoint(mouse_pos):
                return notif_id
                
        return None
    
    def get_notification_by_id(self, notif_id):
        """Return the notification with the given ID"""
        for notification in self.game_state.notifications:
            if notification.get("id") == notif_id:
                return notification
        return None

class BulkPurchasePanel:
    def __init__(self, rect, game_state):
        self.rect = rect
        self.game_state = game_state
        
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Create bulk purchase buttons
        button_width = 50
        button_height = 30
        button_spacing = 10
        
        # X1 button
        self.x1_button = Button(
            pygame.Rect(rect.x, rect.y, button_width, button_height),
            "x1"
        )
        
        # X10 button
        self.x10_button = Button(
            pygame.Rect(rect.x + button_width + button_spacing, rect.y, button_width, button_height),
            "x10"
        )
        
        # X100 button
        self.x100_button = Button(
            pygame.Rect(rect.x + 2 * (button_width + button_spacing), rect.y, button_width, button_height),
            "x100"
        )
        
        # Max button
        self.max_button = Button(
            pygame.Rect(rect.x + 3 * (button_width + button_spacing), rect.y, button_width, button_height),
            "Max"
        )
        
        # Track which button is currently selected
        self.selected_button = self.x1_button
        
    def update(self, mouse_pos):
        # Update all buttons
        self.x1_button.update(mouse_pos)
        self.x10_button.update(mouse_pos)
        self.x100_button.update(mouse_pos)
        self.max_button.update(mouse_pos)
        
    def render(self, surface):
        # Draw panel background
        pygame.draw.rect(surface, PANEL_COLOR, self.rect)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, 1)  # Border
        
        # Draw all buttons
        self.x1_button.render(surface)
        self.x10_button.render(surface)
        self.x100_button.render(surface)
        self.max_button.render(surface)
        
        # Highlight selected button
        if self.selected_button:
            pygame.draw.rect(surface, (255, 255, 0), self.selected_button.rect, 2)
        
    def select_button(self, button):
        """Select a bulk purchase button"""
        self.selected_button = button
        
    def get_multiplier(self):
        """Get the current selected multiplier"""
        if self.selected_button == self.x1_button:
            return 1
        elif self.selected_button == self.x10_button:
            return 10
        elif self.selected_button == self.x100_button:
            return 100
        elif self.selected_button == self.max_button:
            return -1  # Special value for max
        return 1
