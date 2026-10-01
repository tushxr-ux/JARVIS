#version 330 core

in vec3 vColor;
in float vAlpha;
in float vSize;
in vec3 vWorldPos;
in float vType;
in float vDistFromCenter;

out vec4 fragColor;

uniform vec3 uCameraPos;
uniform float uTime;
uniform float uAudioLevel;
uniform bool uMuted;
uniform bool uSpeaking;

void main() {
    // Circular point sprite
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;
    
    // Soft circular falloff
    float alpha = smoothstep(0.5, 0.1, dist);
    
    // Core glow - brighter in center
    float coreGlow = smoothstep(0.5, 0.0, dist);
    
    // Color
    vec3 color = vColor;
    
    // Muted state - red/orange
    if (uMuted) {
        color = mix(color, vec3(1.0, 0.15, 0.05), 0.7);
        alpha *= 0.5;
    }
    
    // Speaking state - brighter, more intense
    if (uSpeaking) {
        color = mix(color, vec3(1.0, 0.5, 0.0), 0.4);
        alpha *= 1.3;
        coreGlow *= 1.5;
    }
    
    // Audio reactive pulse
    float pulse = sin(uTime * 0.01 * 10.0 + vWorldPos.x * 5.0) * 0.1 + 0.9;
    alpha *= pulse * (0.7 + 0.3 * uAudioLevel);
    
    // Rim particles get elongated glow
    if (vType < -0.5) {
        alpha *= 0.7;
        coreGlow *= 2.0;
        color = vec3(1.0, 0.85, 0.3);
    }
    
    // Attractor particles - hot white core
    if (vType > 0.5) {
        coreGlow *= 3.0;
        color = mix(color, vec3(1.0, 1.0, 0.8), 0.5);
    }
    
    // Final color with HDR-style bloom preparation
    vec3 finalColor = color * alpha * (1.0 + coreGlow * 2.0);
    float finalAlpha = vAlpha * alpha * (0.5 + coreGlow * 0.5);
    
    // Additive blending for glow effect
    fragColor = vec4(finalColor, finalAlpha);
}