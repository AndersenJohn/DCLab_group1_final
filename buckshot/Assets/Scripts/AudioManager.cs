using UnityEngine;

public class AudioManager : MonoBehaviour
{
    public static AudioManager I;

    [Header("Audio Sources")]
    public AudioSource ambienceSource;
    public AudioSource sfxSource;

    [Header("Ambience")]
    public AudioClip dungeonLoop;

    [Header("SFX - Common")]
    public AudioClip bulletLoad;
    public AudioClip gunShootLive;
    public AudioClip gunShootBlank;

    [Header("SFX - Items (7)")]
    public AudioClip magnifier;
    public AudioClip cigarette;
    public AudioClip beer;
    public AudioClip saw;
    public AudioClip handcuff;
    public AudioClip phone;
    public AudioClip reverse;

    void Awake()
    {
        if (I == null) I = this;
        else Destroy(gameObject);
    }

    // =============================
    // Ambience
    // =============================
    public void PlayAmbience()
    {
        if (dungeonLoop == null) return;
        ambienceSource.clip = dungeonLoop;
        ambienceSource.loop = true;
        ambienceSource.Play();
    }

    // =============================
    // SFX
    // =============================
    public void PlaySFX(AudioClip clip)
    {
        if (clip == null) return;
        sfxSource.PlayOneShot(clip);
    }
}
