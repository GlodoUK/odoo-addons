from odoo.tests.common import TransactionCase, tagged

from odoo.addons.base_search_rank.fields import apply_word_similarity_threshold


@tagged("post_install", "-at_install")
class TestSearchRankPostgres(TransactionCase):
    """Pin the postgres-level behaviour SearchRank's matching and ranking
    rely on.

    Consumer-facing behaviour (document content, translations, name_search
    integration) is tested in the modules that declare SearchRank fields,
    against their real fields.
    """

    def test_pg_trgm_installed(self):
        self.env.cr.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
        self.assertTrue(
            self.env.cr.fetchone(),
            "pg_trgm must be installed (pre_init_hook should have created it)",
        )

    def test_word_similarity_ranks_exact_first(self):
        # the founding requirement: searching "967" must rank sku=967 above
        # sku=aaa967bb, while both remain findable
        self.env.cr.execute(
            """
            SELECT s, word_similarity('967', s)
            FROM (VALUES ('967'), ('aaa967bb'), ('candle 900')) v(s)
            ORDER BY 2 DESC
            """
        )
        rows = self.env.cr.fetchall()
        self.assertEqual(rows[0][0], "967")
        self.assertEqual(rows[0][1], 1.0)
        by_value = dict(rows)
        self.assertLess(by_value["aaa967bb"], 1.0)

    def test_threshold_admits_misspellings(self):
        apply_word_similarity_threshold(self.env, 0.4)
        self.env.cr.execute(
            "SELECT %s::text <%% %s::text", ["candel", "scented candle large"]
        )
        self.assertTrue(
            self.env.cr.fetchone()[0],
            "candel -> candle must match at the configured threshold"
            " (scores 0.571; the postgres default of 0.6 rejects it)",
        )

    def test_threshold_is_transaction_scoped(self):
        apply_word_similarity_threshold(self.env, 0.4)
        self.env.cr.execute(
            "SELECT current_setting('pg_trgm.word_similarity_threshold')"
        )
        self.assertEqual(float(self.env.cr.fetchone()[0]), 0.4)
