import pygame
from game.constants import PANEL_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, TEXT_COLOR

def render_notification_detail(ui_manager, screen):
    """Render a dialog showing notification details"""
    if not ui_manager.current_notification:
        ui_manager.show_notification_detail = False
        return
        
    # Draw dialog background
    dialog_width = 500
    dialog_height = 250
    dialog_x = (ui_manager.screen_width - dialog_width) // 2
    dialog_y = (ui_manager.screen_height - dialog_height) // 2
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    
    # Draw semi-transparent overlay
    overlay = pygame.Surface((ui_manager.screen_width, ui_manager.screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
    screen.blit(overlay, (0, 0))
    
    # Draw dialog box
    pygame.draw.rect(screen, PANEL_COLOR, dialog_rect)
    pygame.draw.rect(screen, (150, 150, 170), dialog_rect, 2)  # Border
    
    # Get notification type for title
    notification_type = ui_manager.current_notification.get("type", "info").capitalize()
    
    # Draw title
    title_text = ui_manager.title_font.render(f"{notification_type} Notification", True, TEXT_COLOR)
    screen.blit(title_text, (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 20))
    
    # Draw message
    message = ui_manager.current_notification.get("text", "")
    message_surface = ui_manager.font.render(message, True, TEXT_COLOR)
    screen.blit(message_surface, (dialog_x + 20, dialog_y + 60))
    
    # Draw detailed information with word wrapping
    details = ui_manager.current_notification.get("details", "")
    wrapped_text = wrap_text(ui_manager.font, details, dialog_width - 40)
    
    for i, line in enumerate(wrapped_text):
        line_surface = ui_manager.font.render(line, True, TEXT_COLOR)
        screen.blit(line_surface, (dialog_x + 20, dialog_y + 90 + i * 25))
    
    # Draw close button
    close_button_rect = pygame.Rect(dialog_x + (dialog_width - 100) // 2, dialog_y + dialog_height - 50, 100, 30)
    close_button_color = BUTTON_HOVER_COLOR if close_button_rect.collidepoint(ui_manager.mouse_pos) else BUTTON_COLOR
    
    pygame.draw.rect(screen, close_button_color, close_button_rect)
    pygame.draw.rect(screen, (150, 150, 170), close_button_rect, 1)  # Border
    
    close_text = ui_manager.font.render("Close", True, TEXT_COLOR)
    screen.blit(close_text, (close_button_rect.x + (close_button_rect.width - close_text.get_width()) // 2, 
                          close_button_rect.y + (close_button_rect.height - close_text.get_height()) // 2))
    
    return close_button_rect

def handle_notification_detail_click(ui_manager, mouse_pos, close_button_rect):
    """Handle clicks in the notification detail dialog"""
    if close_button_rect.collidepoint(mouse_pos):
        ui_manager.show_notification_detail = False
        return True
    return False

def wrap_text(font, text, max_width):
    """Wrap text to fit within a given width"""
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = font.size(word + ' ')[0]
        
        if current_width + word_width > max_width:
            # Line is full, start a new one
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
