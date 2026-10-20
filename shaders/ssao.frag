#version 300 es
precision highp float;

in vec2 vTexCoord;
layout(location = 0) out float fragOcclusion;

uniform sampler2D uDepthTexture;
uniform sampler2D uNoiseTexture;
uniform mat4 uInverseProjection;
uniform mat4 uProjection;
uniform vec3 uKernel[16];
uniform vec2 uNoiseScale;
uniform float uRadius;
uniform float uBias;
uniform int uSampleCount;

vec3 reconstructViewPosition(vec2 uv, float depth) {
    vec4 clip = vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 view = uInverseProjection * clip;
    return view.xyz / max(abs(view.w), 0.00001) * sign(view.w);
}

void main() {
    float depth = texture(uDepthTexture, vTexCoord).r;
    if (depth >= 0.999999) {
        fragOcclusion = 1.0;
        return;
    }

    vec3 position = reconstructViewPosition(vTexCoord, depth);
    vec3 randomVector = normalize(texture(uNoiseTexture, vTexCoord * uNoiseScale).xyz * 2.0 - 1.0);
    vec3 normal = normalize(cross(dFdx(position), dFdy(position)));
    vec3 tangent = normalize(randomVector - normal * dot(randomVector, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 basis = mat3(tangent, bitangent, normal);
    int sampleCount = clamp(uSampleCount, 1, 16);
    float occluded = 0.0;

    for (int i = 0; i < 16; ++i) {
        if (i >= sampleCount) break;
        vec3 samplePosition = position + basis * uKernel[i] * uRadius;
        vec4 offset = uProjection * vec4(samplePosition, 1.0);
        vec2 sampleUv = offset.xy / offset.w * 0.5 + 0.5;
        if (any(lessThan(sampleUv, vec2(0.0))) || any(greaterThan(sampleUv, vec2(1.0)))) continue;
        float sampleDepth = reconstructViewPosition(sampleUv, texture(uDepthTexture, sampleUv).r).z;
        float rangeWeight = smoothstep(0.0, 1.0, uRadius / max(abs(position.z - sampleDepth), 0.0001));
        occluded += (sampleDepth >= samplePosition.z + uBias ? 1.0 : 0.0) * rangeWeight;
    }
    fragOcclusion = clamp(1.0 - occluded / float(sampleCount), 0.0, 1.0);
}
