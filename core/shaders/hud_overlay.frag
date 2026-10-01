#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform float uTime;
uniform vec4 uMetrics; // cpu, mem, net, gpu/tmp
uniform vec2 uResolution;

void main() {
    vec2 uv = vTexCoord;
    
    // Four corners
    vec2 corners[4] = {
        vec2(0.02, 0.95),   // Top-left (CPU)
        vec2(0.85, 0.95),   // Top-right (MEM)
        vec2(0.02, 0.05),   // Bottom-left (NET)
        vec2(0.78, 0.05)    // Bottom-right (GPU/TMP)
    };
    
    vec3 bgColor = vec3(0.01, 0.01, 0.02);
    vec3 borderColor = vec3(0.0, 0.7, 1.0);
    vec3 textColor = vec3(1.0, 0.72, 0.0);
    vec3 warningColor = vec3(1.0, 0.3, 0.0);
    
    float panelW = 0.18;
    float panelH = 0.045;
    float cornerRadius = 0.005;
    
    vec3 color = bgColor;
    float alpha = 0.0;
    
    for (int i = 0; i < 4; i++) {
        vec2 c = corners[i];
        vec2 rel = (uv - c) / vec2(panelW, panelH);
        
        // Rounded rect SDF
        vec2 d = abs(rel) - vec2(1.0) + vec2(cornerRadius / panelW, cornerRadius / panelH);
        float panel = 1.0 - min(max(d.x, d.y), 0.0) * 100.0;
        panel = clamp(panel, 0.0, 1.0);
        
        if (panel > 0.5) {
            alpha = max(alpha, 0.85);
            color = mix(bgColor, textColor * 0.1, panel * 0.3);
        }
        
        // Border
        float border = 1.0 - smoothstep(0.98, 1.0, max(abs(rel.x), abs(rel.y)));
        if (border > 0.0) {
            color = mix(color, borderColor, border * 0.5);
            alpha = max(alpha, border * 0.5);
        }
    }
    
    // Scanline
    float scan = 1.0 - 0.03 * sin(uv.y * uResolution.y * 0.5 + uTime * 0.01);
    color *= scan;
    
    fragColor = vec4(color, alpha);
}