import pygame

class Camera:
    def __init__(self, screen_width, screen_height, map_width_px=0, map_height_px=0):
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.width = screen_width
        self.height = screen_height
        
        self.map_width_px = map_width_px
        self.map_height_px = map_height_px
        self.zoom_level = 1.0
        
        self._update_viewport_size()

    @property
    def x(self):
        return self.camera_x

    @x.setter
    def x(self, value):
        self.camera_x = value

    @property
    def y(self):
        return self.camera_y

    @y.setter
    def y(self, value):
        self.camera_y = value

    def resize(self, w, h):
        self.width = w
        self.height = h
        self._update_viewport_size()

    def set_zoom(self, zoom):
        self.zoom_level = zoom
        self._update_viewport_size()
        
    def set_bounds(self, width_px, height_px):
        self.map_width_px = width_px
        self.map_height_px = height_px

    def _update_viewport_size(self):
        """Called once when Zoom or Resolution changes"""
        target_w = self.width
        # [Spectator Refinement] Split Screen Limit support if injected
        if hasattr(self, 'view_limit_w') and self.view_limit_w:
            target_w = self.view_limit_w

        if self.zoom_level > 0:
            self.view_w = target_w / self.zoom_level
            self.view_h = self.height / self.zoom_level
        else:
            self.view_w = target_w
            self.view_h = self.height

    def move(self, dx, dy):
        self.camera_x += dx
        self.camera_y += dy

    def update(self, target_x, target_y):
        # [Spectator] Ensure viewport is up to date (in case of dynamic resize)
        self.view_w = self.width / self.zoom_level
        self.view_h = self.height / self.zoom_level

        # Calculate Top-Left based on center target
        x = target_x - self.view_w / 2
        y = target_y - self.view_h / 2

        # Clamp X
        if self.map_width_px > self.view_w:
            x = max(0, min(x, self.map_width_px - self.view_w))
        else:
            # Map smaller than screen -> Center it
            x = -(self.view_w - self.map_width_px) / 2

        # Clamp Y
        if self.map_height_px > self.view_h:
            y = max(0, min(y, self.map_height_px - self.view_h))
        else:
            # Map smaller than screen -> Center it
            y = -(self.view_h - self.map_height_px) / 2

        self.camera_x = x
        self.camera_y = y
