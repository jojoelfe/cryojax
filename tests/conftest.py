import os
import pytest

from jax import random
from jax import config

import cryojax.simulator as cs
from cryojax.io import load_fourier_grid

config.update("jax_enable_x64", True)


@pytest.fixture
def scattering():
    return cs.FourierSliceScattering(shape=(81, 81))


@pytest.fixture
def density():
    filename = os.path.join(
        os.path.dirname(__file__), "data", "3jar_monomer_bfm1_ps5_28.mrc"
    )
    return cs.ElectronGrid.from_file(filename)


@pytest.fixture
def weights_and_coordinates():
    filename = os.path.join(
        os.path.dirname(__file__), "data", "3jar_monomer_bfm1_ps5_28.mrc"
    )
    return load_fourier_grid(filename)


@pytest.fixture
def resolution():
    return 5.32


@pytest.fixture
def filters(scattering):
    return [cs.LowpassFilter(scattering.padded_shape)]
    # return []


@pytest.fixture
def masks(scattering):
    return [cs.CircularMask(scattering.shape)]


@pytest.fixture
def state(resolution):
    return cs.PipelineState(
        pose=cs.EulerPose(degrees=False),
        ice=cs.GaussianIce(key=random.PRNGKey(seed=1)),
        optics=cs.CTFOptics(),
        exposure=cs.UniformExposure(N=1e5, mu=1.0),
        detector=cs.GaussianDetector(
            pixel_size=resolution, key=random.PRNGKey(seed=0)
        ),
    )


@pytest.fixture
def specimen(density, resolution):
    return cs.Specimen(density=density, resolution=resolution)


@pytest.fixture
def scattering_model(scattering, specimen, state, filters, masks):
    return cs.ScatteringImage(
        scattering=scattering,
        specimen=specimen,
        state=state,
        masks=masks,
        filters=filters,
    )


@pytest.fixture
def optics_model(scattering, specimen, state, filters, masks):
    return cs.OpticsImage(
        scattering=scattering,
        specimen=specimen,
        state=state,
        filters=filters,
        masks=masks,
    )


@pytest.fixture
def noisy_model(scattering, specimen, state, filters, masks):
    return cs.GaussianImage(
        scattering=scattering,
        specimen=specimen,
        state=state,
        filters=filters,
        masks=masks,
    )


@pytest.fixture
def maskless_model(scattering, specimen, state, filters):
    return cs.OpticsImage(
        scattering=scattering,
        specimen=specimen,
        state=state,
        filters=filters,
    )

@pytest.fixture
def test_image(noisy_model):
    return noisy_model()


@pytest.fixture
def likelihood_model(scattering, specimen, state, filters, masks, test_image):
    return cs.GaussianImage(
        scattering=scattering,
        specimen=specimen,
        state=state,
        filters=filters,
        masks=masks,
        observed=test_image
    )