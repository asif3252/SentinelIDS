from io import BytesIO
import pandas as pd
import plotly.express as px
import streamlit as st
from sentinel import demo, train, predict, FEATURES, LABELS

st.set_page_config(page_title='SentinelIDS', page_icon='🛡️', layout='wide')
st.title('🛡️ SentinelIDS')
st.caption('AI network intrusion analysis • offline security research workbench')
st.warning('Demo traffic is synthetic. Its metrics do not establish real-world detection performance. Scores are uncalibrated model estimates.')
with st.sidebar:
    st.header('Analysis settings')
    source = st.radio('Training source', ['Synthetic demo', 'Upload labeled CSV'])
    uploaded = st.file_uploader('Training CSV', type='csv') if source != 'Synthetic demo' else None
    algorithm = st.selectbox('Classifier', ['Random Forest', 'Extra Trees'])
    threshold = st.slider('Alert threshold', .05, .95, .50, .05)
    st.caption('Lower thresholds generally generate more alerts. Tune on representative validation traffic before use.')
    st.download_button('Download schema example', demo(30).to_csv(index=False), 'example_flows.csv', 'text/csv')

@st.cache_resource(max_entries=3)
def fit(raw, algorithm):
    return train(pd.read_csv(BytesIO(raw)), algorithm)

if source == 'Upload labeled CSV' and uploaded is None:
    st.info('Upload a labeled flow CSV or select Synthetic demo. Column definitions are in README.md.')
    st.stop()
try:
    raw = demo().to_csv(index=False).encode() if source == 'Synthetic demo' else uploaded.getvalue()
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError('CSV must be under 20 MB.')
    with st.spinner('Training and evaluating classifier…'):
        model, report, cm, importance, splits = fit(raw, algorithm)
    st.caption(f"Source: {source} | {algorithm} | Split sizes: {splits}")
    a, b, c = st.columns(3)
    a.metric('Test macro F1', f"{report['macro avg']['f1-score']:.3f}")
    b.metric('Test attack recall', f"{cm[1:, 1:].sum() / cm[1:, :].sum():.1%}")
    c.metric('Test false-positive rate', f"{cm[0, 1:].sum() / cm[0].sum():.1%}")
    st.caption('Test metrics use the classifier’s highest-probability class, independent of the alert slider.')
    overview, inspect, evaluation = st.tabs(['Traffic analysis', 'Model explanation', 'Evaluation'])
    with overview:
        sample = st.file_uploader('Analyze another CSV (labels optional)', type='csv')
        if sample is not None and sample.size > 20 * 1024 * 1024:
            raise ValueError('Analysis CSV must be under 20 MB.')
        traffic = pd.read_csv(sample) if sample else demo(400, seed=97).drop(columns='label')
        if sample is None:
            st.info('Showing independent synthetic demonstration flows.')
        results = predict(model, traffic, threshold)
        d, e = st.columns(2)
        d.metric('Flows analyzed', len(results))
        e.metric('Threshold alerts', int(results.alert.sum()))
        st.plotly_chart(px.histogram(results, x='prediction', color='prediction'), use_container_width=True)
        only = st.checkbox('Show alerts only')
        st.dataframe(results[results.alert] if only else results, use_container_width=True)
        st.download_button('Export all predictions', results.to_csv(index=False), 'sentinel_predictions.csv', 'text/csv')
        st.subheader('Inspect a flow')
        row = st.number_input('Row position', 0, len(results)-1, 0)
        st.write(results.iloc[int(row)][['prediction', 'attack_score', 'review_priority']])
        st.caption('Feature values below provide investigation context; they are not causal explanations or per-alert attribution.')
        st.dataframe(traffic.iloc[[int(row)]][FEATURES])
    with inspect:
        st.subheader('Validation permutation importance')
        st.caption('Decrease in macro F1 after shuffling a feature, averaged over three repeats. Global model reliance, not an explanation of any individual alert.')
        st.bar_chart(importance.sort_values())
    with evaluation:
        st.plotly_chart(px.imshow(cm, x=LABELS, y=LABELS, text_auto=True, labels={'x':'Predicted', 'y':'Actual'}, title='Held-out test confusion matrix'), use_container_width=True)
        st.dataframe(pd.DataFrame(report).T)
        st.download_button('Export evaluation JSON', __import__('json').dumps({'report': report, 'splits': splits, 'confusion_matrix': cm.tolist()}, indent=2), 'evaluation.json', 'application/json')
except (ValueError, TypeError, KeyError, pd.errors.ParserError) as exc:
    st.error(str(exc))
