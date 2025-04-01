import pygame
import sys
import time
import os
from game.game_state import GameState
from game.ui.ui_manager import UIManager
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, GAME_TITLE

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        
        # Get display info for fullscreen mode
        display_info = pygame.display.Info()
        self.max_width = display_info.current_w
        self.max_height = display_info.current_h
        
        # Set fixed window size (1080p)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.fullscreen = False
        self.resizable = False
        
        # Create window with fixed size
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.last_update_time = time.time()
        
        # Track if window is being resized
        self.is_resizing = False
        self.resize_cooldown = 0
        
        # Initialize game state and UI
        self.game_state = GameState()
        self.ui_manager = UIManager(self.screen, self.game_state)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F11 or (event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_ALT):
                    self.toggle_fullscreen()
            
            # Pass events to UI manager
            self.ui_manager.handle_event(event)
    
    def update(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update game state (idle progression)
        self.game_state.update(elapsed_time)
        
        # Update UI
        self.ui_manager.update()
    
    def render(self):
        # Clear the screen
        self.screen.fill(BACKGROUND_COLOR)
        
        # Render UI
        self.ui_manager.render()
        
        # Update display
        pygame.display.flip()
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            # Switch to fullscreen mode
            self.screen = pygame.display.set_mode((self.max_width, self.max_height), pygame.FULLSCREEN)
            self.width, self.height = self.max_width, self.max_height
        else:
            # Restore windowed mode with fixed 1080p size
            self.width, self.height = SCREEN_WIDTH, SCREEN_HEIGHT
            self.screen = pygame.display.set_mode((self.width, self.height))
        
        # Update UI with new screen dimensions
        self.ui_manager.update_screen_size(self.width, self.height)
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
