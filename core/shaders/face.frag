#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uFace;
uniform float uTime;
uniform float uAudioLevel;
uniform float uScale;
uniform bool uMuted;
uniform bool uSpeaking;

void main() {
    vec2 uv = vTexCoord * 2.0 - 1.0;
    float dist = length(uv);
    
    if (dist > 1.0) discard;
    
    // Sample face texture
    vec4 face = texture(uFace, vTexCoord);
    
    // Circular mask with soft edge
    float mask = smoothstep(1.0, 0.92, dist);
    
    // Pulsing glow ring
    float ring = smoothstep(0.95, 1.0, dist) * (1.0 + uAudioLevel * 2.0);
    ring *= (sin(uTime * 0.001 * 3.0) * 0.3 + 0.7);
    
    // Color grading based on state
    vec3 color = face.rgb;
    if (uMuted) {
        color = mix(color, vec3(1.0, 0.2, 0.1), 0.5);
    } else if (uSpeaking) {
        color = mix(color, vec3(1.0, 0.5, 0.0), 0.3 * uAudioLevel);
    }
    
    // Audio reactive brightness
    color *= (0.8 + 0.2 * uAudioLevel);
    
    // Final composition
    vec3 finalColor = color * mask + vec3(1.0, 0.68, 0.0) * ring;
    float finalAlpha = face.a * mask + ring * 0.5;
    
    fragColor = vec4(finalColor, finalAlpha);
}