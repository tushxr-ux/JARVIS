#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uTexture;
uniform float uTime;
uniform float uAudioLevel;
uniform bool uMuted;
uniform bool uSpeaking;
uniform vec2 uCenter;
uniform float uRadius;

void main() {
    vec2 uv = vTexCoord;
    vec2 center = uCenter;
    float radius = uRadius;
    
    vec2 toCenter = uv - center;
    float dist = length(toCenter) / radius;
    
    // Multi-layered glow
    float glow = 0.0;
    
    // Core
    glow += smoothstep(0.8, 0.0, dist) * 0.6;
    // Middle
    glow += smoothstep(1.2, 0.5, dist) * 0.3;
    // Outer
    glow += smoothstep(2.0, 1.0, dist) * 0.1;
    
    // Audio reactivity
    glow *= (1.0 + uAudioLevel * 1.5);
    
    // Pulsing
    float pulse = sin(uTime * 0.001 * 1.5) * 0.1 + 0.9;
    glow *= pulse;
    
    // Color
    vec3 color;
    if (uMuted) {
        color = vec3(1.0, 0.15, 0.05);
    } else if (uSpeaking) {
        color = mix(vec3(1.0, 0.7, 0.0), vec3(1.0, 0.3, 0.0), uAudioLevel);
    } else {
        color = vec3(1.0, 0.68, 0.0);
    }
    
    vec3 finalColor = color * glow;
    
    fragColor = vec4(finalColor, glow);
}