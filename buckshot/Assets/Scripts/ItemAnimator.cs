using UnityEngine;
using System.Collections;

public enum ItemSide { Blue, Red }
public class ItemAnimator : MonoBehaviour
{
    Animator anim;
    ItemSlot ownerSlot;
    Coroutine destroyRoutine;

    void Awake()
    {
        anim = GetComponent<Animator>();
        ownerSlot = GetComponentInParent<ItemSlot>();
    }

    public void Play(ItemSide side)
    {
        if (anim == null) return;

        // 播動畫
        if (side == ItemSide.Blue)
            anim.Play("Blue");
        else
            anim.Play("Red");

        if (destroyRoutine != null)
            StopCoroutine(destroyRoutine);

        destroyRoutine = StartCoroutine(DestroyAfterSeconds(3f));
    }

    IEnumerator DestroyAfterSeconds(float seconds)
    {
        yield return new WaitForSeconds(seconds);

        if (ownerSlot != null)
        {
            ownerSlot.takenBy = null;
            ownerSlot.takenByName = null;
        }

        Destroy(gameObject);
    }
}
