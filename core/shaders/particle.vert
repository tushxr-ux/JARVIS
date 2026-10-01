#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aVelocity;
layout(location = 2) in float aSize;
layout(location = 3) in vec3 aColor;
layout(location = 4) in float aLife;
layout(location = 5) in float aType;

uniform mat4 uMVP;
uniform float uTime;
uniform float uAudioLevel;
uniform vec3 uCenter;
uniform float uSphereRadius;
uniform int uParticleCount;

out vec3 vColor;
out float vAlpha;
out float vSize;
out vec3 vWorldPos;
out float vType;
out float vDistFromCenter;

void main() {
    // Particle simulation on GPU
    float t = uTime * 0.001; // Convert to seconds
    
    // Base position (pre-computed on CPU for initial distribution)
    vec3 pos = aPosition;
    vec3 vel = aVelocity;
    
    // Audio reactivity
    float audioBoost = 1.0 + uAudioLevel * 2.0;
    
    // Orbital motion around center
    float orbitSpeed = 0.3 + aType * 0.5;
    float orbitRadius = length(pos - uCenter);
    vec3 toCenter = normalize(uCenter - pos);
    vec3 tangent = normalize(cross(toCenter, vec3(0.0, 1.0, 0.0)));
    if (length(tangent) < 0.1) tangent = normalize(cross(toCenter, vec3(1.0, 0.0, 0.0)));
    
    // Spiral motion
    float angle = t * orbitSpeed * audioBoost + aLife * 100.0;
    vec3 orbitalPos = uCenter + rotateY(toCenter * orbitRadius, angle);
    
    // Attractor vortices (5 dynamic attractors)
    vec3 finalPos = orbitalPos;
    for (int i = 0; i < 5; i++) {
        float attractorPhase = t * 0.6 + float(i) * 1.3;
        vec3 attractorPos = vec3(
            sin(attractorPhase) * 0.5,
            cos(attractorPhase * 0.7) * 0.3,
            cos(attractorPhase) * 0.5
        ) * uSphereRadius * 0.8;
        
        vec3 toAttractor = attractorPos - finalPos;
        float dist = length(toAttractor);
        if (dist < uSphereRadius * 0.4) {
            float force = exp(-dist / (uSphereRadius * 0.1)) * 0.3 * audioBoost;
            finalPos += normalize(toAttractor) * force;
        }
    }
    
    // Surface wave deformation
    float wave = sin(finalPos.x * 3.0 + t * 2.0) * 0.05 +
                 cos(finalPos.z * 2.5 - t * 1.5) * 0.04 +
                 sin(finalPos.y * 4.0 + t * 1.8) * 0.03;
    finalPos += normalize(finalPos - uCenter) * wave * uSphereRadius * audioBoost;
    
    // Breathing scale
    float breath = 1.0 + sin(t * 0.8) * 0.02 + uAudioLevel * 0.15;
    finalPos = uCenter + (finalPos - uCenter) * breath;
    
    // Rim spikes (ferrofluid effect)
    vec3 toCenterNorm = normalize(finalPos - uCenter);
    float rimFactor = smoothstep(0.85, 1.0, length(finalPos - uCenter) / uSphereRadius);
    finalPos += toCenterNorm * rimFactor * (0.15 + uAudioLevel * 0.3) * uSphereRadius;
    
    vWorldPos = finalPos;
    vDistFromCenter = length(finalPos - uCenter) / uSphereRadius;
    
    // Projection
    vec4 clipPos = uMVP * vec4(finalPos, 1.0);
    gl_Position = clipPos;
    
    // Point size with perspective correction
    float baseSize = aSize * (1.0 + uAudioLevel * 0.5);
    vSize = baseSize * (300.0 / -clipPos.z);
    vSize = clamp(vSize, 1.0, 8.0);
    
    // Color based on type and depth
    vType = aType;
    vec3 depthColor = mix(vec3(1.0, 0.7, 0.0), vec3(1.0, 0.3, 0.0), vDistFromCenter);
    vec3 heatColor = vec3(1.0, 0.8, 0.1);
    
    if (aType > 0.5) {
        // Attractor/heat particles
        vColor = mix(depthColor, heatColor, 0.7);
        vAlpha = 0.9;
    } else if (aType < -0.5) {
        // Rim spike particles
        vColor = vec3(1.0, 0.9, 0.4);
        vAlpha = 0.6;
    } else {
        // Core particles
        vColor = mix(aColor, depthColor, 0.5);
        vAlpha = 0.7 + 0.3 * (1.0 - vDistFromCenter);
    }
    
    // Audio pulse
    vAlpha *= (0.6 + 0.4 * uAudioLevel);
    vAlpha *= (0.5 + 0.5 * sin(t * 8.0 + aLife * 50.0));
}

// Helper: rotate vector around Y axis
vec3 rotateY(vec3 v, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec3(v.x * c + v.z * s, v.y, -v.x * s + v.z * c);
}