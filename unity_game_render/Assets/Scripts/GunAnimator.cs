using UnityEngine;

public enum GunSide { Blue, Red }

public class GunAnimator : MonoBehaviour
{
    private Animator anim;

    void Awake()
    {
        anim = GetComponent<Animator>();
    }

    public void PlayShoot(GunSide shooter, GunSide target, int damage)
    {
        anim.Rebind();
        anim.Update(0f);
        if (anim == null) return;
        
        string animName = $"{shooter}Shoot{target}-{damage}DMG";
        anim.Play(animName);
    }
    public void PlayRegrow()
    {
        if (anim == null) return;

        string animName = $"BarrelRegrow";
        anim.Play(animName);
    }
}