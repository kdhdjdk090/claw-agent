use std::future::Future;
use std::pin::Pin;

use crate::error::ApiError;
use crate::types::{MessageRequest, MessageResponse};

pub mod claw_provider;
pub mod openai_compat;

pub type ProviderFuture<'a, T> = Pin<Box<dyn Future<Output = Result<T, ApiError>> + Send + 'a>>;

pub trait Provider {
    type Stream;

    fn send_message<'a>(
        &'a self,
        request: &'a MessageRequest,
    ) -> ProviderFuture<'a, MessageResponse>;

    fn stream_message<'a>(
        &'a self,
        request: &'a MessageRequest,
    ) -> ProviderFuture<'a, Self::Stream>;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProviderKind {
    ClawApi,
    Xai,
    OpenAi,
    OpenAiCodex,
    Alibaba,
    DeepSeek,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ProviderMetadata {
    pub provider: ProviderKind,
    pub auth_env: &'static str,
    pub base_url_env: &'static str,
    pub default_base_url: &'static str,
}

const MODEL_REGISTRY: &[(&str, ProviderMetadata)] = &[
    (
        "opus",
        ProviderMetadata {
            provider: ProviderKind::ClawApi,
            auth_env: "ANTHROPIC_API_KEY",
            base_url_env: "ANTHROPIC_BASE_URL",
            default_base_url: claw_provider::DEFAULT_BASE_URL,
        },
    ),
    (
        "sonnet",
        ProviderMetadata {
            provider: ProviderKind::ClawApi,
            auth_env: "ANTHROPIC_API_KEY",
            base_url_env: "ANTHROPIC_BASE_URL",
            default_base_url: claw_provider::DEFAULT_BASE_URL,
        },
    ),
    (
        "haiku",
        ProviderMetadata {
            provider: ProviderKind::ClawApi,
            auth_env: "ANTHROPIC_API_KEY",
            base_url_env: "ANTHROPIC_BASE_URL",
            default_base_url: claw_provider::DEFAULT_BASE_URL,
        },
    ),
    (
        "claude-opus-4-6",
        ProviderMetadata {
            provider: ProviderKind::ClawApi,
            auth_env: "ANTHROPIC_API_KEY",
            base_url_env: "ANTHROPIC_BASE_URL",
            default_base_url: claw_provider::DEFAULT_BASE_URL,
        },
    ),
    (
        "claude-sonnet-4-6",
        ProviderMetadata {
            provider: ProviderKind::ClawApi,
            auth_env: "ANTHROPIC_API_KEY",
            base_url_env: "ANTHROPIC_BASE_URL",
            default_base_url: claw_provider::DEFAULT_BASE_URL,
        },
    ),
    (
        "claude-haiku-4-5-20251213",
        ProviderMetadata {
            provider: ProviderKind::ClawApi,
            auth_env: "ANTHROPIC_API_KEY",
            base_url_env: "ANTHROPIC_BASE_URL",
            default_base_url: claw_provider::DEFAULT_BASE_URL,
        },
    ),
    (
        "grok",
        ProviderMetadata {
            provider: ProviderKind::Xai,
            auth_env: "XAI_API_KEY",
            base_url_env: "XAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_XAI_BASE_URL,
        },
    ),
    (
        "grok-3",
        ProviderMetadata {
            provider: ProviderKind::Xai,
            auth_env: "XAI_API_KEY",
            base_url_env: "XAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_XAI_BASE_URL,
        },
    ),
    (
        "grok-mini",
        ProviderMetadata {
            provider: ProviderKind::Xai,
            auth_env: "XAI_API_KEY",
            base_url_env: "XAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_XAI_BASE_URL,
        },
    ),
    (
        "grok-3-mini",
        ProviderMetadata {
            provider: ProviderKind::Xai,
            auth_env: "XAI_API_KEY",
            base_url_env: "XAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_XAI_BASE_URL,
        },
    ),
    (
        "grok-2",
        ProviderMetadata {
            provider: ProviderKind::Xai,
            auth_env: "XAI_API_KEY",
            base_url_env: "XAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_XAI_BASE_URL,
        },
    ),
    (
        "gpt-5.3-codex",
        ProviderMetadata {
            provider: ProviderKind::OpenAiCodex,
            auth_env: "CODEX_HOME/auth.json",
            base_url_env: "OPENAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_OPENAI_BASE_URL,
        },
    ),
    (
        "gpt-5-codex",
        ProviderMetadata {
            provider: ProviderKind::OpenAiCodex,
            auth_env: "CODEX_HOME/auth.json",
            base_url_env: "OPENAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_OPENAI_BASE_URL,
        },
    ),
    (
        "codex-mini-latest",
        ProviderMetadata {
            provider: ProviderKind::OpenAiCodex,
            auth_env: "CODEX_HOME/auth.json",
            base_url_env: "OPENAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_OPENAI_BASE_URL,
        },
    ),
    (
        "qwen-plus",
        ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        },
    ),
    (
        "qwen3-max",
        ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        },
    ),
    (
        "qwen3-coder-plus",
        ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        },
    ),
    (
        "qwen3-coder-480b-a35b-instruct",
        ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        },
    ),
    (
        "qwen3.5-397b-a17b",
        ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        },
    ),
    (
        "qwen3-235b-a22b",
        ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        },
    ),
    (
        "deepseek-chat",
        ProviderMetadata {
            provider: ProviderKind::DeepSeek,
            auth_env: "DEEPSEEK_API_KEY",
            base_url_env: "DEEPSEEK_BASE_URL",
            default_base_url: openai_compat::DEFAULT_DEEPSEEK_BASE_URL,
        },
    ),
    (
        "deepseek-reasoner",
        ProviderMetadata {
            provider: ProviderKind::DeepSeek,
            auth_env: "DEEPSEEK_API_KEY",
            base_url_env: "DEEPSEEK_BASE_URL",
            default_base_url: openai_compat::DEFAULT_DEEPSEEK_BASE_URL,
        },
    ),
    (
        "deepseek-coder",
        ProviderMetadata {
            provider: ProviderKind::DeepSeek,
            auth_env: "DEEPSEEK_API_KEY",
            base_url_env: "DEEPSEEK_BASE_URL",
            default_base_url: openai_compat::DEFAULT_DEEPSEEK_BASE_URL,
        },
    ),
];

fn provider_hint(model: &str) -> Option<ProviderKind> {
    let lower = model.trim().to_ascii_lowercase();
    if lower.starts_with("openai-codex/") || lower.starts_with("codex/") {
        return Some(ProviderKind::OpenAiCodex);
    }
    if lower.starts_with("openai/") {
        return Some(ProviderKind::OpenAi);
    }
    if lower.starts_with("alibaba/") || lower.starts_with("dashscope/") {
        return Some(ProviderKind::Alibaba);
    }
    if lower.starts_with("deepseek/") {
        return Some(ProviderKind::DeepSeek);
    }
    None
}

fn strip_provider_prefix(model: &str) -> &str {
    let trimmed = model.trim();
    if let Some((_, suffix)) = trimmed.split_once('/') {
        if provider_hint(trimmed).is_some() {
            return suffix;
        }
    }
    trimmed
}

fn is_codex_model(model: &str) -> bool {
    model.to_ascii_lowercase().contains("codex")
}

fn is_alibaba_model(model: &str) -> bool {
    model.to_ascii_lowercase().starts_with("qwen")
}

fn is_deepseek_model(model: &str) -> bool {
    model.to_ascii_lowercase().starts_with("deepseek")
}

#[must_use]
pub fn resolve_model_alias(model: &str) -> String {
    let trimmed = strip_provider_prefix(model);
    let lower = trimmed.to_ascii_lowercase();
    MODEL_REGISTRY
        .iter()
        .find_map(|(alias, metadata)| {
            (*alias == lower).then_some(match metadata.provider {
                ProviderKind::ClawApi => match *alias {
                    "opus" => "claude-opus-4-6",
                    "sonnet" => "claude-sonnet-4-6",
                    "haiku" => "claude-haiku-4-5-20251213",
                    _ => trimmed,
                },
                ProviderKind::Xai => match *alias {
                    "grok" | "grok-3" => "grok-3",
                    "grok-mini" | "grok-3-mini" => "grok-3-mini",
                    "grok-2" => "grok-2",
                    _ => trimmed,
                },
                ProviderKind::OpenAi
                | ProviderKind::OpenAiCodex
                | ProviderKind::Alibaba
                | ProviderKind::DeepSeek => trimmed,
            })
        })
        .map_or_else(|| trimmed.to_string(), ToOwned::to_owned)
}

#[must_use]
pub fn metadata_for_model(model: &str) -> Option<ProviderMetadata> {
    if let Some(provider) = provider_hint(model) {
        return Some(match provider {
            ProviderKind::OpenAi => ProviderMetadata {
                provider,
                auth_env: "OPENAI_API_KEY",
                base_url_env: "OPENAI_BASE_URL",
                default_base_url: openai_compat::DEFAULT_OPENAI_BASE_URL,
            },
            ProviderKind::OpenAiCodex => ProviderMetadata {
                provider,
                auth_env: "CODEX_HOME/auth.json",
                base_url_env: "OPENAI_BASE_URL",
                default_base_url: openai_compat::DEFAULT_OPENAI_BASE_URL,
            },
            ProviderKind::Alibaba => ProviderMetadata {
                provider,
                auth_env: "DASHSCOPE_API_KEY",
                base_url_env: "DASHSCOPE_BASE_URL",
                default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
            },
            ProviderKind::DeepSeek => ProviderMetadata {
                provider,
                auth_env: "DEEPSEEK_API_KEY",
                base_url_env: "DEEPSEEK_BASE_URL",
                default_base_url: openai_compat::DEFAULT_DEEPSEEK_BASE_URL,
            },
            ProviderKind::ClawApi | ProviderKind::Xai => unreachable!("invalid provider hint"),
        });
    }

    let canonical = resolve_model_alias(model);
    let lower = canonical.to_ascii_lowercase();
    if let Some((_, metadata)) = MODEL_REGISTRY.iter().find(|(alias, _)| *alias == lower) {
        return Some(*metadata);
    }
    if is_alibaba_model(&lower) {
        return Some(ProviderMetadata {
            provider: ProviderKind::Alibaba,
            auth_env: "DASHSCOPE_API_KEY",
            base_url_env: "DASHSCOPE_BASE_URL",
            default_base_url: openai_compat::DEFAULT_ALIBABA_BASE_URL,
        });
    }
    if is_deepseek_model(&lower) {
        return Some(ProviderMetadata {
            provider: ProviderKind::DeepSeek,
            auth_env: "DEEPSEEK_API_KEY",
            base_url_env: "DEEPSEEK_BASE_URL",
            default_base_url: openai_compat::DEFAULT_DEEPSEEK_BASE_URL,
        });
    }
    if lower.starts_with("grok") {
        return Some(ProviderMetadata {
            provider: ProviderKind::Xai,
            auth_env: "XAI_API_KEY",
            base_url_env: "XAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_XAI_BASE_URL,
        });
    }
    if is_codex_model(&lower) {
        return Some(ProviderMetadata {
            provider: ProviderKind::OpenAiCodex,
            auth_env: "CODEX_HOME/auth.json",
            base_url_env: "OPENAI_BASE_URL",
            default_base_url: openai_compat::DEFAULT_OPENAI_BASE_URL,
        });
    }
    None
}

#[must_use]
pub fn detect_provider_kind(model: &str) -> ProviderKind {
    if let Some(provider) = provider_hint(model) {
        return provider;
    }
    if let Some(metadata) = metadata_for_model(model) {
        return metadata.provider;
    }
    if claw_provider::has_auth_from_env_or_saved().unwrap_or(false) {
        return ProviderKind::ClawApi;
    }
    if openai_compat::has_codex_auth() {
        let canonical = resolve_model_alias(model);
        if is_codex_model(&canonical) {
            return ProviderKind::OpenAiCodex;
        }
    }
    if openai_compat::has_api_key("OPENAI_API_KEY") {
        return ProviderKind::OpenAi;
    }
    if openai_compat::has_api_key("XAI_API_KEY") {
        return ProviderKind::Xai;
    }
    if openai_compat::has_api_key("DASHSCOPE_API_KEY") {
        return ProviderKind::Alibaba;
    }
    if openai_compat::has_api_key("DEEPSEEK_API_KEY") {
        return ProviderKind::DeepSeek;
    }
    ProviderKind::ClawApi
}

#[must_use]
pub fn max_tokens_for_model(model: &str) -> u32 {
    let canonical = resolve_model_alias(model);
    if canonical.contains("opus") {
        32_000
    } else {
        64_000
    }
}

#[cfg(test)]
mod tests {
    use super::{detect_provider_kind, max_tokens_for_model, resolve_model_alias, ProviderKind};

    #[test]
    fn resolves_grok_aliases() {
        assert_eq!(resolve_model_alias("grok"), "grok-3");
        assert_eq!(resolve_model_alias("grok-mini"), "grok-3-mini");
        assert_eq!(resolve_model_alias("grok-2"), "grok-2");
        assert_eq!(resolve_model_alias("openai-codex/gpt-5.3-codex"), "gpt-5.3-codex");
        assert_eq!(resolve_model_alias("dashscope/qwen-plus"), "qwen-plus");
        assert_eq!(resolve_model_alias("deepseek/deepseek-reasoner"), "deepseek-reasoner");
    }

    #[test]
    fn detects_provider_from_model_name_first() {
        assert_eq!(detect_provider_kind("grok"), ProviderKind::Xai);
        assert_eq!(
            detect_provider_kind("openai-codex/gpt-5.3-codex"),
            ProviderKind::OpenAiCodex
        );
        assert_eq!(detect_provider_kind("qwen-plus"), ProviderKind::Alibaba);
        assert_eq!(detect_provider_kind("deepseek-reasoner"), ProviderKind::DeepSeek);
        assert_eq!(
            detect_provider_kind("claude-sonnet-4-6"),
            ProviderKind::ClawApi
        );
    }

    #[test]
    fn keeps_existing_max_token_heuristic() {
        assert_eq!(max_tokens_for_model("opus"), 32_000);
        assert_eq!(max_tokens_for_model("grok-3"), 64_000);
    }
}
