"""CmdStan method generate_quantities tests"""

import contextlib
import json
import logging
import os
import unittest
from importlib import reload

import numpy as np
import pandas as pd
from numpy.testing import assert_array_equal, assert_raises
from testfixtures import LogCapture

import cmdstanpy.stanfit
from cmdstanpy.cmdstan_args import Method
from cmdstanpy.model import CmdStanModel

HERE = os.path.dirname(os.path.abspath(__file__))
DATAFILES_PATH = os.path.join(HERE, 'data')


@contextlib.contextmanager
def without_import(library, module):
    with unittest.mock.patch.dict('sys.modules', {library: None}):
        reload(module)
        yield
    reload(module)


class GenerateQuantitiesTest(unittest.TestCase):
    def test_from_csv_files(self):
        # fitted_params sample - list of filenames
        goodfiles_path = os.path.join(DATAFILES_PATH, 'runset-good', 'bern')
        csv_files = []
        for i in range(4):
            csv_files.append('{}-{}.csv'.format(goodfiles_path, i + 1))

        # gq_model
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')

        bern_gqs = model.generate_quantities(data=jdata, mcmc_sample=csv_files)

        self.assertEqual(
            bern_gqs.runset._args.method, Method.GENERATE_QUANTITIES
        )
        self.assertIn('CmdStanGQ: model=bernoulli_ppc', bern_gqs.__repr__())
        self.assertIn('method=generate_quantities', bern_gqs.__repr__())

        self.assertEqual(bern_gqs.runset.chains, 4)
        for i in range(bern_gqs.runset.chains):
            self.assertEqual(bern_gqs.runset._retcode(i), 0)
            csv_file = bern_gqs.runset.csv_files[i]
            self.assertTrue(os.path.exists(csv_file))

        column_names = [
            'y_rep[1]',
            'y_rep[2]',
            'y_rep[3]',
            'y_rep[4]',
            'y_rep[5]',
            'y_rep[6]',
            'y_rep[7]',
            'y_rep[8]',
            'y_rep[9]',
            'y_rep[10]',
        ]
        self.assertEqual(bern_gqs.column_names, tuple(column_names))

        # draws()
        self.assertEqual(bern_gqs.draws().shape, (100, 4, 10))
        with LogCapture() as log:
            logging.getLogger()
            bern_gqs.draws(inc_warmup=True)
        log.check_present(
            (
                'cmdstanpy',
                'WARNING',
                "Sample doesn't contain draws from warmup iterations, "
                'rerun sampler with "save_warmup=True".',
            )
        )

        # draws_pd()
        self.assertEqual(bern_gqs.draws_pd().shape, (400, 10))
        self.assertEqual(
            bern_gqs.draws_pd(inc_sample=True).shape[1],
            bern_gqs.mcmc_sample.draws_pd().shape[1]
            + bern_gqs.draws_pd().shape[1],
        )

    def test_from_csv_files_bad(self):
        # gq model
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')

        # no filename
        with self.assertRaises(ValueError):
            model.generate_quantities(data=jdata, mcmc_sample=[])

        # Stan CSV flles corrupted
        goodfiles_path = os.path.join(
            DATAFILES_PATH, 'runset-bad', 'bad-draws-bern'
        )
        csv_files = []
        for i in range(4):
            csv_files.append('{}-{}.csv'.format(goodfiles_path, i + 1))

        with self.assertRaisesRegex(
            Exception, 'Invalid sample from Stan CSV files'
        ):
            model.generate_quantities(data=jdata, mcmc_sample=csv_files)

    def test_from_mcmc_sample(self):
        # fitted_params sample
        stan = os.path.join(DATAFILES_PATH, 'bernoulli.stan')
        bern_model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')
        bern_fit = bern_model.sample(
            data=jdata,
            chains=4,
            parallel_chains=2,
            seed=12345,
            iter_sampling=100,
        )
        # gq_model
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)

        bern_gqs = model.generate_quantities(data=jdata, mcmc_sample=bern_fit)

        self.assertEqual(
            bern_gqs.runset._args.method, Method.GENERATE_QUANTITIES
        )
        self.assertIn('CmdStanGQ: model=bernoulli_ppc', bern_gqs.__repr__())
        self.assertIn('method=generate_quantities', bern_gqs.__repr__())
        self.assertEqual(bern_gqs.runset.chains, 4)
        for i in range(bern_gqs.runset.chains):
            self.assertEqual(bern_gqs.runset._retcode(i), 0)
            csv_file = bern_gqs.runset.csv_files[i]
            self.assertTrue(os.path.exists(csv_file))

    def test_from_mcmc_sample_draws(self):
        stan = os.path.join(DATAFILES_PATH, 'bernoulli.stan')
        bern_model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')
        bern_fit = bern_model.sample(
            data=jdata,
            chains=4,
            parallel_chains=2,
            seed=12345,
            iter_sampling=100,
        )
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)

        bern_gqs = model.generate_quantities(data=jdata, mcmc_sample=bern_fit)

        self.assertEqual(bern_gqs.draws_pd().shape, (400, 10))
        self.assertEqual(
            bern_gqs.draws_pd(inc_sample=True).shape[1],
            bern_gqs.mcmc_sample.draws_pd().shape[1]
            + bern_gqs.draws_pd().shape[1],
        )
        row1_sample_pd = bern_fit.draws_pd().iloc[0]
        row1_gqs_pd = bern_gqs.draws_pd().iloc[0]
        self.assertTrue(
            np.array_equal(
                pd.concat((row1_sample_pd, row1_gqs_pd), axis=0).values,
                bern_gqs.draws_pd(inc_sample=True).iloc[0].values,
            )
        )
        # draws_xr
        xr_data = bern_gqs.draws_xr()
        self.assertEqual(xr_data.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0'))
        self.assertEqual(xr_data.y_rep.values.shape, (4, 100, 10))

        xr_var = bern_gqs.draws_xr(vars='y_rep')
        self.assertEqual(xr_var.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0'))
        self.assertEqual(xr_var.y_rep.values.shape, (4, 100, 10))

        xr_var = bern_gqs.draws_xr(vars=['y_rep'])
        self.assertEqual(xr_var.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0'))
        self.assertEqual(xr_var.y_rep.values.shape, (4, 100, 10))

        xr_data_plus = bern_gqs.draws_xr(inc_sample=True)
        self.assertEqual(
            xr_data_plus.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0')
        )
        self.assertEqual(xr_data_plus.y_rep.values.shape, (4, 100, 10))
        self.assertEqual(xr_data_plus.theta.dims, ('chain', 'draw'))
        self.assertEqual(xr_data_plus.theta.values.shape, (4, 100))

    def test_from_mcmc_sample_variables(self):
        stan = os.path.join(DATAFILES_PATH, 'bernoulli.stan')
        bern_model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')
        bern_fit = bern_model.sample(
            data=jdata,
            chains=4,
            parallel_chains=2,
            seed=12345,
            iter_sampling=100,
        )
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)

        bern_gqs = model.generate_quantities(data=jdata, mcmc_sample=bern_fit)

        theta = bern_gqs.stan_variable(var='theta')
        self.assertEqual(theta.shape, (400,))
        y_rep = bern_gqs.stan_variable(var='y_rep')
        self.assertEqual(y_rep.shape, (400, 10))
        with self.assertRaises(ValueError):
            bern_gqs.stan_variable(var='eta')
        with self.assertRaises(ValueError):
            bern_gqs.stan_variable(var='lp__')
        with self.assertRaises(ValueError):
            bern_gqs.stan_variable(var='lp__', name='theta')

        with LogCapture() as log:
            self.assertEqual(bern_gqs.stan_variable(name='theta').shape, (400,))
        log.check_present(
            (
                'cmdstanpy',
                'WARNING',
                'Keyword "name" is deprecated, use "var" instead.',
            )
        )

        vars_dict = bern_gqs.stan_variables()
        var_names = list(
            bern_gqs.mcmc_sample.metadata.stan_vars_cols.keys()
        ) + list(bern_gqs.metadata.stan_vars_cols.keys())
        self.assertEqual(set(var_names), set(list(vars_dict.keys())))

    def test_save_warmup(self):
        # fitted_params sample
        stan = os.path.join(DATAFILES_PATH, 'bernoulli.stan')
        bern_model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')
        bern_fit = bern_model.sample(
            data=jdata,
            chains=4,
            parallel_chains=2,
            seed=12345,
            iter_warmup=100,
            iter_sampling=100,
            save_warmup=True,
        )
        # gq_model
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)

        with LogCapture() as log:
            logging.getLogger()
            bern_gqs = model.generate_quantities(
                data=jdata, mcmc_sample=bern_fit
            )
        log.check_present(
            (
                'cmdstanpy',
                'WARNING',
                'Sample contains saved warmup draws which will be used to '
                'generate additional quantities of interest.',
            )
        )
        self.assertEqual(bern_gqs.draws().shape, (100, 4, 10))
        self.assertEqual(
            bern_gqs.draws(concat_chains=False, inc_warmup=False).shape,
            (100, 4, 10),
        )
        self.assertEqual(
            bern_gqs.draws(concat_chains=False, inc_warmup=True).shape,
            (200, 4, 10),
        )
        self.assertEqual(
            bern_gqs.draws(concat_chains=True, inc_warmup=False).shape,
            (400, 10),
        )
        self.assertEqual(
            bern_gqs.draws(concat_chains=True, inc_warmup=True).shape,
            (800, 10),
        )

        self.assertEqual(bern_gqs.draws_pd().shape, (400, 10))
        self.assertEqual(bern_gqs.draws_pd(inc_warmup=False).shape, (400, 10))
        self.assertEqual(bern_gqs.draws_pd(inc_warmup=True).shape, (800, 10))
        self.assertEqual(
            bern_gqs.draws_pd(vars=['y_rep'], inc_warmup=False).shape,
            (400, 10),
        )
        self.assertEqual(
            bern_gqs.draws_pd(vars='y_rep', inc_warmup=False).shape,
            (400, 10),
        )

        theta = bern_gqs.stan_variable(var='theta')
        self.assertEqual(theta.shape, (400,))
        y_rep = bern_gqs.stan_variable(var='y_rep')
        self.assertEqual(y_rep.shape, (400, 10))
        with self.assertRaises(ValueError):
            bern_gqs.stan_variable(var='eta')
        with self.assertRaises(ValueError):
            bern_gqs.stan_variable(var='lp__')

        vars_dict = bern_gqs.stan_variables()
        var_names = list(
            bern_gqs.mcmc_sample.metadata.stan_vars_cols.keys()
        ) + list(bern_gqs.metadata.stan_vars_cols.keys())
        self.assertEqual(set(var_names), set(list(vars_dict.keys())))

        xr_data = bern_gqs.draws_xr()
        self.assertEqual(xr_data.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0'))
        self.assertEqual(xr_data.y_rep.values.shape, (4, 100, 10))

        xr_data_plus = bern_gqs.draws_xr(inc_sample=True)
        self.assertEqual(
            xr_data_plus.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0')
        )
        self.assertEqual(xr_data_plus.y_rep.values.shape, (4, 100, 10))
        self.assertEqual(xr_data_plus.theta.dims, ('chain', 'draw'))
        self.assertEqual(xr_data_plus.theta.values.shape, (4, 100))

        xr_data_plus = bern_gqs.draws_xr(vars='theta', inc_sample=True)
        self.assertEqual(xr_data_plus.theta.dims, ('chain', 'draw'))
        self.assertEqual(xr_data_plus.theta.values.shape, (4, 100))

        xr_data_plus = bern_gqs.draws_xr(inc_sample=True, inc_warmup=True)
        self.assertEqual(
            xr_data_plus.y_rep.dims, ('chain', 'draw', 'y_rep_dim_0')
        )
        self.assertEqual(xr_data_plus.y_rep.values.shape, (4, 200, 10))
        self.assertEqual(xr_data_plus.theta.dims, ('chain', 'draw'))
        self.assertEqual(xr_data_plus.theta.values.shape, (4, 200))

    def test_sample_plus_quantities_dedup(self):
        # fitted_params - model GQ block: y_rep is PPC of theta
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')
        bern_fit = model.sample(
            data=jdata,
            chains=4,
            parallel_chains=2,
            seed=12345,
            iter_sampling=100,
        )
        # gq_model - y_rep[n] == y[n]
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc_dup.stan')
        model = CmdStanModel(stan_file=stan)
        bern_gqs = model.generate_quantities(data=jdata, mcmc_sample=bern_fit)
        # check that models have different y_rep values
        assert_raises(
            AssertionError,
            assert_array_equal,
            bern_fit.stan_variable(var='y_rep'),
            bern_gqs.stan_variable(var='y_rep'),
        )
        # check that stan_variable returns values from gq model
        with open(jdata) as fd:
            bern_data = json.load(fd)
        y_rep = bern_gqs.stan_variable(var='y_rep')
        for i in range(10):
            self.assertEqual(y_rep[0, i], bern_data['y'][i])

    def test_deprecated(self):
        goodfiles_path = os.path.join(DATAFILES_PATH, 'runset-good', 'bern')
        csv_files = []
        for i in range(4):
            csv_files.append('{}-{}.csv'.format(goodfiles_path, i + 1))

        # gq_model
        stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
        model = CmdStanModel(stan_file=stan)
        jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')

        bern_gqs = model.generate_quantities(data=jdata, mcmc_sample=csv_files)
        with LogCapture() as log:
            self.assertEqual(bern_gqs.generated_quantities.shape, (400, 10))
        log.check_present(
            (
                'cmdstanpy',
                'WARNING',
                'Property "generated_quantities" has been deprecated, '
                'use method "draws" instead.',
            )
        )
        with LogCapture() as log:
            self.assertEqual(bern_gqs.generated_quantities_pd.shape, (400, 10))
        log.check_present(
            (
                'cmdstanpy',
                'WARNING',
                'Property "generated_quantities_pd" has been deprecated, '
                'use method "draws_pd" instead.',
            )
        )

    def test_no_xarray(self):
        with without_import('xarray', cmdstanpy.stanfit):
            with self.assertRaises(ImportError):
                # if this fails the testing framework is the problem
                import xarray as _  # noqa

            stan = os.path.join(DATAFILES_PATH, 'bernoulli.stan')
            bern_model = CmdStanModel(stan_file=stan)
            jdata = os.path.join(DATAFILES_PATH, 'bernoulli.data.json')
            bern_fit = bern_model.sample(
                data=jdata,
                chains=4,
                parallel_chains=2,
                seed=12345,
                iter_sampling=100,
            )
            stan = os.path.join(DATAFILES_PATH, 'bernoulli_ppc.stan')
            model = CmdStanModel(stan_file=stan)

            bern_gqs = model.generate_quantities(
                data=jdata, mcmc_sample=bern_fit
            )

            with self.assertRaises(RuntimeError):
                bern_gqs.draws_xr()


if __name__ == '__main__':
    unittest.main()
