package at.petrak.hexcasting.common.casting.operators

import at.petrak.hexcasting.api.misc.MediaConstants
import at.petrak.hexcasting.api.spell.Action
import at.petrak.hexcasting.api.spell.ConstMediaAction
import at.petrak.hexcasting.api.spell.asActionResult
import at.petrak.hexcasting.api.spell.casting.CastingContext
import at.petrak.hexcasting.api.spell.getVec3
import at.petrak.hexcasting.api.spell.iota.Iota
import at.petrak.hexcasting.api.spell.iota.NullIota
import net.minecraft.world.level.ClipContext
import net.minecraft.world.phys.HitResult
import net.minecraft.world.phys.Vec3

object OpBlockAxisRaycast : ConstMediaAction {
    override val argc = 2
    override val mediaCost = MediaConstants.DUST_UNIT / 100
    override fun execute(args: List<Iota>, ctx: CastingContext): List<Iota> {
        val origin = args.getVec3(0, argc)
        val look = args.getVec3(1, argc)

        ctx.assertVecInRange(origin)

        val blockHitResult = ctx.world.clip(
            ClipContext(
                origin,
                Action.raycastEnd(origin, look),
                ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,
                ctx.caster
            )
        )

        return if (blockHitResult.type == HitResult.Type.BLOCK && ctx.isVecInRange(Vec3.atCenterOf(blockHitResult.blockPos))) {
            blockHitResult.direction.step().asActionResult
        } else {
            listOf(NullIota())
        }
    }
}