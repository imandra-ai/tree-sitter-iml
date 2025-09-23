# pyright: basic
# pyright: ignore[reportInvalidTypeForm]
# %%
import os

import dotenv
import imandrax_api
from agents.code_logician.base.region_decomp import (
    DecomposeReqData,
    RegionDecomp,
)
from agents.code_logician.base.vg import (
    VG,
    VerifyReqData,
)
from rich import print
from utils.imandra.imandrax.proto_models import (
    DecomposeRes,
    VerifyRes,
)
from utils.imandra.imandrax.proto_to_dict import proto_to_dict

from iml_query.processing import (
    extract_decomp_reqs,
    extract_instance_reqs,
    extract_verify_reqs,
    iml_outline,
)
from iml_query.tree_sitter_utils import get_parser

dotenv.load_dotenv('.env')

iml = """
let add_one (x: int) : int = x + 1
[@@decomp top ()]

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2

let decomp_double = double
[@@decomp top ~assuming: [%id is_positive] ~prune: true ()]

let square : int -> int = ()
[@@opaque]

let cube : int -> int = ()
[@@opaque]

axiom positive_addition x =
  x >= 0 ==> add_one x > x

theorem double_add_one x =
  double (add_one x) = add_one (add_one x) + x
[@@by auto]

verify (fun x -> x > 0 ==> double x > x)

let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

verify double_non_negative_is_increasing

instance (fun x -> x >= 0 ==> not (double x > x))


let two_x = (let x = 1 in double x)

eval (double 2)
"""


async def main():
    print(iml_outline(iml))

    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf-8'))
    iml_wo_vq, new_tree, verify_reqs = extract_verify_reqs(iml, tree)
    iml_wo_iq, new_tree, instance_reqs = extract_instance_reqs(iml, tree)
    iml_wo_dq, new_tree, decomp_reqs = extract_decomp_reqs(iml, tree)

    imls = [iml_wo_vq, iml_wo_iq, iml_wo_dq]

    async with imandrax_api.AsyncClient(
        url=imandrax_api.url_prod,
        auth_token=os.environ['IMANDRAX_API_KEY'],
    ) as c:
        _eval_res = await c.eval_src(iml)

        decomp_results, verify_results = await asyncio.gather(
            asyncio.gather(
                *[c.decompose(**decomp_req) for decomp_req in decomp_reqs]
            ),
            asyncio.gather(
                *[c.verify_src(**verify_req) for verify_req in verify_reqs]
            ),
        )

    # Fill region decomps
    region_decomps = []
    for decomp_req, decomp_res in zip(decomp_reqs, decomp_results, strict=True):
        decomp_req_data_model = DecomposeReqData(**decomp_req)
        decomp_res_model = DecomposeRes.model_validate(
            proto_to_dict(decomp_res)
        )
        region_decomps.append(
            RegionDecomp(
                data=decomp_req_data_model,
                res=decomp_res_model,
            )
        )

    # Fill vgs
    vgs = []
    for verify_req, verify_res in zip(verify_reqs, verify_results, strict=True):
        verify_req_data_model = VerifyReqData(
            predicate=verify_req['src'], kind='verify'
        )
        verify_res_model = VerifyRes.model_validate(proto_to_dict(verify_res))
        vgs.append(
            VG(
                data=verify_req_data_model,
                res=verify_res_model,
            )
        )

    return region_decomps, vgs, imls


if __name__ == '__main__':
    import asyncio

    region_decomps, vgs, imls = asyncio.run(main())

    for i in region_decomps:
        print(i)
    for i in vgs:
        print(i)

    print('=' * 40)

    print('IML without verify reqs')
    print(imls[0])
    print('=' * 40)

    print('IML without instance reqs')
    print(imls[1])
    print('=' * 40)

    print('IML without deocmp reqs')
    print(imls[2])
    print('=' * 40)
