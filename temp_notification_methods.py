def _render_notification_detail(self, surface):
    """Render a detailed view of the selected notification"""
    # Get the notification details
    notification = self.current_notification
    if not notification:
        self.show_notification_detail = False
        return None
        
    # Calculate dialog dimensions and position
    dialog_width = 500
    dialog_height = 300
    dialog_x = (self.screen_width - dialog_width) // 2
    dialog_y = (self.screen_height - dialog_height) // 2
    
    # Draw dialog background
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(surface, PANEL_COLOR, dialog_rect)
    pygame.draw.rect(surface, (150, 150, 170), dialog_rect, 2)  # Border
    
    # Draw title
    title = notification.get("title", "Notification")
    title_surface = self.title_font.render(title, True, TEXT_COLOR)
    surface.blit(title_surface, (dialog_x + (dialog_width - title_surface.get_width()) // 2, dialog_y + 20))
    
    # Draw notification text (with wrapping)
    text = notification.get("detail", notification.get("text", "No details available."))
    
    # Simple text wrapping
    max_width = dialog_width - 40
    lines = []
    current_line = ""
    
    for word in text.split():
        test_line = current_line + (" " if current_line else "") + word
        if self.font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Draw wrapped text
    for i, line in enumerate(lines):
        text_surface = self.font.render(line, True, TEXT_COLOR)
        surface.blit(text_surface, (dialog_x + 20, dialog_y + 70 + i * 25))
    
    # Draw close button
    close_button_rect = pygame.Rect(dialog_x + (dialog_width - 100) // 2, dialog_y + dialog_height - 50, 100, 30)
    close_button_color = BUTTON_HOVER_COLOR if close_button_rect.collidepoint(self.mouse_pos) else BUTTON_COLOR
    
    pygame.draw.rect(surface, close_button_color, close_button_rect)
    pygame.draw.rect(surface, (150, 150, 170), close_button_rect, 1)  # Border
    
    # Draw button text
    close_text = self.font.render("Close", True, TEXT_COLOR)
    surface.blit(close_text, (close_button_rect.x + (close_button_rect.width - close_text.get_width()) // 2, 
                             close_button_rect.y + (close_button_rect.height - close_text.get_height()) // 2))
    
    return close_button_rect

def _handle_notification_detail_click(self, mouse_pos, close_button_rect):
    """Handle clicks in the notification detail view"""
    if close_button_rect and close_button_rect.collidepoint(mouse_pos):
        self.show_notification_detail = False
        return True
    return False
